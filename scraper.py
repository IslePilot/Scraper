from urllib2 import urlopen
import re
from yahoo_finance import Share



from bs4 import BeautifulSoup
from matplotlib import ticker
from pandas.io.data import _adjust_prices

class StockData(object):
    HEADER = "Ticker,Price,Drug,Indication,Phase,Date,Catalyst,Mean Recommendation,Strong Buy,Buy,Recommendation Count,Target Min,Target Mean,Target High,Growth,Market Cap,Short Ratio\n"
    
    def __init__(self, ticker, price, drug, indication, phase, date, catalyst):
        self.ticker = ticker
        self.price = price
        self.drug = drug
        self.indication = indication
        self.phase = phase
        self.date = date
        self.catalyst = catalyst
        
        return
    
    def add_stock_data(self):
        stock = Share(self.ticker)
        cap = stock.get_market_cap()
        if re.search("M", cap) != None:
            self.market_cap = float(cap.strip("M"))*1000000
        elif re.search("B", cap) != None:
            self.market_cap = float(cap.strip("B"))*1000000000
        else:
            self.market_cap = float(cap)
        self.short_ratio = float(stock.get_short_ratio())
        
        print "Market Cap: %.3f"%self.market_cap
        print "Short ratio: %.2f"%self.short_ratio
        
        return
    
    def add_analyst_data(self, recommendation_mean, strong_buy, buy, current_price, \
            target_low, target_mean, target_high, target_growth):
        self.recommendation_mean = recommendation_mean
        self.strong_buy = strong_buy
        self.buy = buy
        self.rec_count = strong_buy+buy 
        self.price2 = current_price
        self.target_low = target_low
        self.target_mean = target_mean
        self.target_high = target_high
        self.target_growth = target_growth
        return
    
    def get_csv(self):
        string = "%s,"%self.ticker
        string += "%.2f,"%self.price
        string += "%s,"%self.drug
        string += "%s,"%self.indication
        string += "%s,"%self.phase
        string += "%s,"%self.date
        string += "%s,"%self.catalyst
        string += "%.1f,"%self.recommendation_mean
        string += "%d,"%self.strong_buy
        string += "%d,"%self.buy
        string += "%d,"%self.rec_count
        string += "%.2f,"%self.target_low
        string += "%.2f,"%self.target_mean
        string += "%.2f,"%self.target_high
        string += "%.1f,"%self.target_growth
        string += "%.3f,"%self.market_cap
        string += "%.2f"%self.short_ratio
        string += "\n"
        return string
    
class FDACatalysts(object):
    def __init__(self):
        # the webpage we want doesn't allow scraping, so we need to manually go
        # to the page, view the source, and then copy it to a file.  
        with open(r"C:\py_scripts\Scraper\biopharmcatalyst.html", "r") as f:
            r = f.read()

        # make soup
        self.soup = BeautifulSoup(r)
        
        # parse the data
        self.parse_html()
        
        return
    
    def parse_html(self):
        """Parse the web data loaded during object creation.
        
        returns: dictionary of {ticker:StockData}"""
        stock_info = self.soup.find_all("tr")
        
        count = 0
        self.stock_list = []
        for stock in stock_info:
            s1 = stock.findAll("td")
            
            if len(s1) > 0:
                count += 1
                ticker = s1[0].get_text()
                price =  float(s1[1].find_all("div", class_="price")[0].get_text().split("$")[1])
                drug = s1[2].find_all("strong", class_="drug")[0].get_text()
                indication = s1[2].find_all("div", class_="indication")[0].get_text().replace(",", " ")
                phase =  s1[3].get_text().encode("ascii", "ignore").strip()
                date_string =  s1[4].find_all("time", class_="catalyst-date")[0].get_text()
                catalyst =  s1[4].find_all("div", class_="catalyst-note")[0].get_text().replace(",", " ")
                
                # build our StockData object
                self.stock_list.append(StockData(ticker, price, drug, 
                                                 indication, phase, date_string, catalyst))
                print "Count = %d"%count
                print "Ticker = %s"%ticker
                print "Price = %.2f"%price
                print "Drug = %s"%drug
                print "Indication = %s"%indication
                print "Phase = %s"%phase
                print "Date = %s"%date_string
                print "Catalyst = %s"%catalyst
            print "============================================================================"

        return

class AnalystData(object):
    def __init__(self, ticker):
        self.ticker = ticker
        
        # build the link
        self.url = "https://finance.yahoo.com/quote/%s/analysts?p=%s"%(ticker, ticker)
        
        # get the webpage text
        self.html = urlopen(self.url).read()
        
        self.parse_html()
        
        return
    
    def parse_html(self):
        # find the average recommendation
        # {"recommendationMean":{"raw":1.7,"fmt":"1.70"}}
        self.recommendation_mean = float(self.get_string("recommendationMean").split('"')[5])
        #print "Recommendation Mean: %.2f"%self.recommendation_mean
        
        # {"recommendationTrend":{"trend":[{"period":"0m","strongBuy":3,"buy":6,"hold":0,"sell":0,"strongSell":0},{"period":"-1m","strongBuy":3,"buy":5,"hold":0,"sell":0,"strongSell":0},{"period":"-2m","strongBuy":3,"buy":5,"hold":0,"sell":0,"strongSell":0},{"period":"-3m","strongBuy":3,"buy":6,"hold":0,"sell":0,"strongSell":0}],"maxAge":86400}
        data = self.get_string("recommendationTrend")
        parsed_data = re.split(":|,", data)
        
        self.strong_buy = int(parsed_data[4])
        self.buy = int(parsed_data[6])
        
        #print "Strong Buy: %d"%self.strong_buy
        #print "Buy: %d"%self.buy
        self.rec_count = self.strong_buy + self.buy
        #print "Reccomendation Count: %d"%self.rec_count
        
        # "currentPrice":{"raw":25.76,"fmt":"25.76"}
        self.current_price = float(self.get_string("currentPrice").split('"')[5])
        #print "Current Price: %.2f"%self.current_price
        
        # "targetLowPrice":{"raw":37,"fmt":"37.00"}
        self.target_low = float(self.get_string("targetLowPrice").split('"')[5])
        #print "Target Low Price: %.2f"%self.target_low
        
        # "targetMeanPrice":{"raw":39.22,"fmt":"39.22"}
        self.target_mean = float(self.get_string("targetMeanPrice").split('"')[5])
        #print "Target Mean Price: %.2f"%self.target_mean
        
        # "targetHighPrice":{"raw":44,"fmt":"44.00"}
        self.target_high = float(self.get_string("targetHighPrice").split('"')[5])
        #print "Target High Price: %.2f"%self.target_high
        
        self.target_growth = 100.0*(self.target_mean-self.current_price)/self.current_price
        #print "Target Growth %.1f%%"%self.target_growth
        
        print "%s: Growth:%.1f MeanRecommendation:%.1f AnalystCount:%d"%(self.ticker,
                                                                         self.target_growth,
                                                                         self.recommendation_mean,
                                                                         self.rec_count)
        return
    
    def get_string(self, key):
        # the format is always "key":{string}
        # find the location of the key
        key_start = self.html.find(key)
        open_brace = self.html.find("{", key_start)
        close_brace = self.html.find("}", open_brace)
        return self.html[open_brace:close_brace+1]
    
    def get_data(self):
        return self.recommendation_mean, self.strong_buy, self.buy, self.current_price, \
            self.target_low, self.target_mean, self.target_high, self.target_growth


if __name__ == '__main__':
    # get our list of stocks to process
    stock_list = FDACatalysts().stock_list
    
    # open our output file and add a header
    csv_file = open(r"C:\py_scripts\Scraper\data.csv", "w")
    csv_file.write(StockData.HEADER)
    
    count = 0
    for stock in stock_list:
        count += 1
        stock.add_stock_data()
        adata = AnalystData(stock.ticker)
        stock.add_analyst_data(*adata.get_data())
        print stock.get_csv()
        csv_file.write(stock.get_csv())
        if count >= 20:
            break
    


    