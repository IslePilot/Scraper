from urllib2 import urlopen
import re
from collections import namedtuple

DataPoint = namedtuple("DataPoint", "ticker growth avg_rec analyst_count")

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
        
        self.data_point = DataPoint(self.ticker,
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
    
    

if __name__ == '__main__':
    AnalystData("FLXN")
    AnalystData("SRNE")
    AnalystData("PTLA")
    