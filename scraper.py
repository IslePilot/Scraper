import urllib2
import re
import datetime
from bs4 import BeautifulSoup
from collections import namedtuple


class StockData(object):
    HEADER = "Ticker,Price ($),Drug,Indication,Phase,Date(YMD),Catalyst,Mean Recommendation,Strong Buy,Buy,Recommendation Count,Target Min($),Target Mean($),Target High($),Growth(%),Market Cap($),Short Percent of Float(%)\n"
    
    def __init__(self, ticker, price, drug, indication, phase, date, catalyst):
        self.ticker = ticker
        self.price = price
        self.drug = drug
        self.indication = indication
        self.phase = phase
        self.date = date
        self.catalyst = catalyst
        return
    
    def add_analyst_data(self, recommendation_mean, strong_buy, buy, current_price, \
            target_low, target_mean, target_high, target_growth, short_percent, market_cap):
        self.recommendation_mean = recommendation_mean
        self.strong_buy = strong_buy
        self.buy = buy
        self.rec_count = strong_buy+buy 
        self.price2 = current_price
        self.target_low = target_low
        self.target_mean = target_mean
        self.target_high = target_high
        self.target_growth = target_growth
        self.short_percent = short_percent
        self.market_cap = market_cap
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
        string += "%.2f"%self.short_percent
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
        self.url2 = "https://finance.yahoo.com/quote/%s/key-statistics?p=%s"%(ticker,ticker)
        
        # get the webpage text
        self.html = urllib2.urlopen(self.url).read()
        self.html2 = urllib2.urlopen(self.url2).read()
        
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
        self.short_percent = 0.0
        self.market_cap = 0.0
        
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
        
        # "shortPercentOfFloat":{"raw":0.244,"fmt":"24.40%"}
        l = self.get_string("shortPercentOfFloat", 2).split('"')
        if len(l) > 5:
            self.short_percent = float(l[2].strip(":,"))*100.0
        
        # "marketCap":{"raw":331165120,"fmt":"331.17M"}
        l = self.get_string("marketCap", 2).split('"')
        if len(l) > 2:
            self.market_cap = float(l[2].strip(":,"))
        
        
        print "%s: Growth:%.1f MeanRecommendation:%.1f AnalystCount:%d"%(self.ticker,
                                                                         self.target_growth,
                                                                         self.recommendation_mean,
                                                                         self.rec_count)
        return
    
    def get_string(self, key, urltext=1):
        if urltext == 1:
            html = self.html
        else:
            html = self.html2
        # the format is always "key":{string}
        # examples:
        # "targetLowPrice":{"raw":37,"fmt":"37.00"}
        # "targetLowPrice":{}
        # find the location of the key
        key_start = html.find(key)
        open_brace = html.find("{", key_start)
        close_brace = html.find("}", open_brace)
        return html[open_brace:close_brace+1]
    
    def get_data(self):
        return self.recommendation_mean, self.strong_buy, self.buy, self.current_price, self.target_low, self.target_mean, self.target_high, self.target_growth, self.short_percent, self.market_cap


if __name__ == '__main__':
    # get our list of stocks to process
    stock_list = FDACatalysts().stock_list
    
    # open our output file and add a header
    now = datetime.datetime.utcnow()
    filename = "c:\\py_scripts\\Scraper\\%s_StockData.csv"%now.strftime("%Y%m%d_%H%M%S")
    csv_file = open(filename, "w")
    csv_file.write(StockData.HEADER)
    
    # define the limits
    price_min = 2.00
    date_end = datetime.datetime(year=2018, month=2, day=28).date()
    rec_max = 2.0
    count_min = 4
    growth_min = 50.0
    market_cap_max = 1500.0e6
    
    SDTuple = namedtuple("SDTuple", "ticker price drug indication phase date catalyst rec_mean sbuy buy count tlow tmean thigh tgrowth cap short")
    outname = "C:\\py_scripts\\Scraper\\%s_TargetStocks.csv"%now.strftime("%Y%m%d_%H%M%S")
    outfile = open(outname, "w")
    outfile.write("Price Min($),%.2f\n"%price_min)
    outfile.write("End Date,%s\n"%date_end.strftime("%Y-%m-%d"))
    outfile.write("Max Mean Recommendation,%.1f\n"%rec_max)
    outfile.write("Minimum Recommendation Count,%d\n"%count_min)
    outfile.write("Minimum Growth(%%),%.1f\n"%growth_min)
    outfile.write("Maximum Market Cap($M),%.1f\n"%market_cap_max)
    outfile.write("\n")
    outfile.write(StockData.HEADER)
    outfile.write("\n")
    
    count = 0
    for stock in stock_list:
        count += 1

        print "%d: %s"%(count, stock.ticker)
        adata = AnalystData(stock.ticker)
        stock.add_analyst_data(*adata.get_data())
        line = stock.get_csv()
        print line
        csv_file.write(line)
        
        # do we want this line?
        sd = SDTuple(*line.strip().split(","))
        if sd.ticker != "Ticker" and \
           price_min <= float(sd.price) and \
           rec_max >= float(sd.rec_mean) and \
           count_min <= int(sd.count) and \
           growth_min <= float(sd.tgrowth) and \
           market_cap_max >= float(sd.cap) and \
           date_end >= datetime.datetime.strptime(sd.date, "%Y-%m-%d").date():
            # put this in our file
            string  = ",".join(map(str, sd))
            string += "\n"
            print string
            outfile.write(string)
    
    outfile.close()
    csv_file.close()
    


    