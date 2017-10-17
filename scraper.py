import urllib2
import re
from yahoo_finance import Share
import datetime
from bs4 import BeautifulSoup
from networkx.algorithms.flow.capacityscaling import capacity_scaling


class StockData(object):
    HEADER = "Ticker,Price ($),Drug,Indication,Phase,Date(YMD),Catalyst,Mean Recommendation,Strong Buy,Buy,Recommendation Count,Target Min($),Target Mean($),Target High($),Growth(%),Market Cap(M),Short Ratio(Months)\n"
    
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
        while True:
            try:
                stock = Share(self.ticker)
                break
            except:
                print "Error reading Yahoo: %s...retrying <<<<<<<<<<<<<<<<<<<<<<<<<<"%self.ticker
                pass
        
        cap = stock.get_market_cap()
        if cap != None:
            if re.search("M", cap) != None:
                self.market_cap = float(cap.strip("M"))
            elif re.search("B", cap) != None:
                self.market_cap = float(cap.strip("B"))*1000.0
            else:
                self.market_cap = float(cap)/1000000.0
        else:
            self.market_cap = 0.0
        
        sr = stock.get_short_ratio()
        if sr != None:
            self.short_ratio = float(sr)
        else:
            self.short_ratio = 0.0
        
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
        string += "%s,"%self.date.strftime("%Y-%m-%d")
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
        url = "https://www.biopharmcatalyst.com/calendars/fda-calendar"
        
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(url, None, headers)
        r = urllib2.urlopen(req).read()
        
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
        ticker = ""
        price = 0.0
        drug = ""
        indication = ""
        phase = ""
        date = None
        catalyst = ""
        self.stock_list = []
        for stock in stock_info:
            th = stock.find_all('th')
            if len(th) > 0:
                print "Found Header Record"
                print "============================================================================"  
                continue
            
            count += 1
            
            for a in stock.find_all('a', class_="ticker"):
                ticker =  a.get_text().strip().encode("ascii", "ingore")
            
            for div in stock.find_all('div', class_="price"):
                price = float(div.get_text().split("$")[1])
            
            for strong in stock.find_all('strong', class_='drug'):
                drug = strong.get_text().strip().replace(",", " ").replace("\n"," ").encode("ascii", "ignore")
            
            for div in stock.find_all('div', class_='indication'):
                indication = div.get_text().strip().replace(",", " ").replace("\n"," ").encode("ascii", "ignore")
            
            for td in stock.find_all('td', class_="stage"):
                phase = td.get_text().strip().encode("ascii", "ignore")
            
            for time in stock.find_all('time', class_="catalyst-date"):
                d = time.get_text().strip()
                date = datetime.datetime.strptime(d, "%m/%d/%Y").date()
            
            for div in stock.find_all('div', class_="catalyst-note"):
                catalyst = div.get_text().strip().replace(",", " ").replace("\n"," ").encode("ascii", "ignore")
            
            print "Ticker = %s"%ticker
            print "Price = %.2f"%price
            print "Drug = %s"%drug
            print "Indication = %s"%indication
            print "Phase = %s"%phase
            print "Date = %s"%date.strftime("%m/%d/%Y")
            print "Catalyst = %s"%catalyst
            print "Count = %d"%count
            print "============================================================================"   

            # build our StockData object
            self.stock_list.append(StockData(ticker, price, drug, indication, phase, date, catalyst))
        
        return

class AnalystData(object):
    def __init__(self, ticker):
        self.ticker = ticker
        
        # build the link
        self.url = "https://finance.yahoo.com/quote/%s/analysts?p=%s"%(ticker, ticker)
        
        # get the webpage text
        self.html = urllib2.urlopen(self.url).read()
        
        self.parse_html()
        
        return
    
    def parse_html(self):
        self.recommendation_mean = 0.0
        self.strong_buy = 0
        self.buy = 0
        self.rec_count = 0
        self.target_low = 0.0
        self.target_mean = 0.0
        self.target_high = 0.0
        self.current_price = 0.0
        self.target_growth = 0.0
        
        # find the average recommendation
        # {"recommendationMean":{"raw":1.7,"fmt":"1.70"}}
        l = self.get_string("recommendationMean").split('"')
        if len(l) > 5:
            self.recommendation_mean = float(l[5])
        #print "Recommendation Mean: %.2f"%self.recommendation_mean
        
        # {"recommendationTrend":{"trend":[{"period":"0m","strongBuy":3,"buy":6,"hold":0,"sell":0,"strongSell":0},{"period":"-1m","strongBuy":3,"buy":5,"hold":0,"sell":0,"strongSell":0},{"period":"-2m","strongBuy":3,"buy":5,"hold":0,"sell":0,"strongSell":0},{"period":"-3m","strongBuy":3,"buy":6,"hold":0,"sell":0,"strongSell":0}],"maxAge":86400}
        data = self.get_string("recommendationTrend")
        parsed_data = re.split(":|,", data)
        if len(parsed_data) > 6:
            self.strong_buy = int(parsed_data[4])
            self.buy = int(parsed_data[6])
            self.rec_count = self.strong_buy + self.buy
        #print "Strong Buy: %d"%self.strong_buy
        #print "Buy: %d"%self.buy
        #print "Reccomendation Count: %d"%self.rec_count
        
        # "targetLowPrice":{"raw":37,"fmt":"37.00"}
        l = self.get_string("targetLowPrice").split('"')
        if len(l) > 5:
            self.target_low = float(l[5])
        #print "Target Low Price: %.2f"%self.target_low
        
        # "targetMeanPrice":{"raw":39.22,"fmt":"39.22"}
        l = self.get_string("targetMeanPrice").split('"')
        if len(l) > 5:
            self.target_mean = float(l[5])
        #print "Target Mean Price: %.2f"%self.target_mean
        
        # "targetHighPrice":{"raw":44,"fmt":"44.00"}
        l = self.get_string("targetHighPrice").split('"')
        if len(l) > 5:
            self.target_high = float(l[5])
        #print "Target High Price: %.2f"%self.target_high
        
        # "currentPrice":{"raw":25.76,"fmt":"25.76"}
        l = self.get_string("currentPrice").split('"')
        if len(l) > 5:
            self.current_price = float(l[5])
            self.target_growth = 100.0*(self.target_mean-self.current_price)/self.current_price
        #print "Target Growth %.1f%%"%self.target_growth
        #print "Current Price: %.2f"%self.current_price
        
        print "%s: Growth:%.1f MeanRecommendation:%.1f AnalystCount:%d"%(self.ticker,
                                                                         self.target_growth,
                                                                         self.recommendation_mean,
                                                                         self.rec_count)
        return
    
    def get_string(self, key):
        # the format is always "key":{string}
        # examples:
        # "targetLowPrice":{"raw":37,"fmt":"37.00"}
        # "targetLowPrice":{}
        # find the location of the key
        key_start = self.html.find(key)
        open_brace = self.html.find("{", key_start)
        close_brace = self.html.find("}", open_brace)
        return self.html[open_brace:close_brace+1]
    
    def get_data(self):
        return self.recommendation_mean, self.strong_buy, self.buy, self.current_price, self.target_low, self.target_mean, self.target_high, self.target_growth


if __name__ == '__main__':
    # get our list of stocks to process
    stock_list = FDACatalysts().stock_list
    
    # open our output file and add a header
    now = datetime.datetime.utcnow()
    filename = "c:\\py_scripts\\Scraper\\%s_StockData.csv"%now.strftime("%Y%m%d_%H%M%S")
    csv_file = open(filename, "w")
    csv_file.write(StockData.HEADER)
    
    count = 0
    for stock in stock_list:
        count += 1
        if count >= 0:
            print "%d: %s"%(count, stock.ticker)
            stock.add_stock_data()
            adata = AnalystData(stock.ticker)
            stock.add_analyst_data(*adata.get_data())
            print stock.get_csv()
            csv_file.write(stock.get_csv())

    


    