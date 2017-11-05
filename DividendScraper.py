#!/usr/bin/env python

"""
Copyright (C) 2017 AeroSys Engineering, Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See <http://www.gnu.org/licenses/>.

Revision History:
    Nov 5, 2017: keith, created
"""
import urllib2
import ast
import re
import datetime
from collections import namedtuple

STOCK_CALENDAR = namedtuple("STOCK_CALENDAR", "date type value")


class DataScraper(object):
    HEADER = "ticker,start_date,start_price,end_date,end_price,drip_yield,value_growth\n"
    
    def __init__(self, ticker):
        self.ticker = ticker
        
        # build the URL:
        url = "https://finance.yahoo.com/quote/%s/history?p=%s"%(ticker, ticker)
        
        # don't look like a scraper...
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(url, None, headers)
        r = urllib2.urlopen(req).read()

        # get the price/dividend/split data
        self.get_data(r)
        
        return

    
    def get_data(self, source):
        # first find where the price data starts
        # "HistoricalPriceStore":{"prices":[{
        s = source.find('"HistoricalPriceStore"')
        
        # find the opening brace
        start = source.find("[", s)
        
        # now find the closing brace
        end = source.find("]", start)

        parsed = source[start+2:end-1]
        
        date_list = re.split(r"},{", parsed)
        
        print "Lines of data: %d"%len(date_list)
        
        # parse each line
        self.prices = {}
        self.dividends = {}
        self.splits = {}
        self.end_date = None
        self.start_date = None
        for d  in date_list:
            # parse each string into a dictionary
            try:
                d = ast.literal_eval("{"+d+"}")
            except:
                print "Unable to parse: %s"%d
                continue
            
            # there are three types of lines, they all have a date though, convert the date from a UNIX timestamp to a real date
            date = datetime.datetime.fromtimestamp(int(d["date"]))
            
            # find our first data
            if self.end_date == None:
                self.end_date = date
            
            # find our last date
            self.start_date = date
            
            # parse the rest of the line
            if d.has_key("close"):
                # price info line:  we want "date" and "close"
                # {"date":1505827800,"open":20.549999237060547,"high":20.709999084472656,"low":20.34000015258789,"close":20.469999313354492,
                # "volume":1007200,"adjclose":20.469999313354492}
                self.prices[date] = float(d["close"])
            elif d.has_key("type"):
                if d["type"] == "DIVIDEND":
                    # "DIVIDEND" line: we want "date" and "amount"
                    # {"amount":0.4,"date":1505827800,"type":"DIVIDEND","data":0.4}
                    self.dividends[date] = float(d["amount"])
                elif d["type"] == "SPLIT":
                    # "SPLIT" line: we want "date" and "split"
                    # {"date":1505827800,"numerator":100,"denominator":105,"splitRatio":"105\u002F100","type":"SPLIT","data":"105\u002F100"}
                    self.splits[date] = float(d["denominator"])/float(d["numerator"])
                else:
                    print "Unknown type:"
                    print d
            else:
                print "Unknown line:"
                print d
        return

    def drip_yield(self):
        global STOCK_CALENDAR
        
        # build a calendar of shares per share due to dividends
        calendar = []
        for key, value in sorted(self.dividends.items()):
            # get the price on the day in question
            price = self.prices[key]
            
            # now compute how many shares you get for each share of stock
            div = value/price
            
            # save the data
            calendar.append(STOCK_CALENDAR(key, "DIVIDEND", div))
        
        # now insert the split data in the calendar.  If we already have a dividend on
        # the date, insert it after the dividend
        for date, splits in sorted(self.splits.items()):
            # look through the calendar to find the index where this belongs
            index = 0
            for i in range(len(calendar)):
                if calendar[i].date <= date:
                    index = i+1
            
            # now insert the data in the calendar
            calendar.insert(index, STOCK_CALENDAR(key, "SPLIT", splits))
        
        # now we need to calculate the growth in the number of shares (this is a DRIP model)
        # start with one share
        shares = 1.0
        
        for c in calendar:
            if c.type == 'DIVIDEND':
                shares += shares*c.value
            elif c.type == 'SPLIT':
                shares *= c.value
            else:
                print "Unknown calendar entry"
        
        # find the start and end prices
        start_price = self.prices[self.start_date]
        end_price = self.prices[self.end_date]
        
        # finally, compute the growth in value
        drip_yield = shares - 1
        growth = (end_price*shares - start_price) / start_price
        
        # build our string to return
        # ticker,start_date,start_price,end_date,end_price,drip_yield,value_growth
        stock_str = self.ticker + ","
        stock_str += "%s,$%.2f,"%(self.start_date.strftime("%m/%d/%Y"), start_price)
        stock_str += "%s,$%.2f,"%(self.end_date.strftime("%m/%d/%Y"), end_price)
        stock_str += "%.4f,%.4f"%(drip_yield, growth)
        print stock_str
        stock_str += "\n"

        return stock_str
    
if __name__ == '__main__':
    # get the list of stocks to analyze
    with open(r"C:\py_scripts\Scraper\DividendStockTickers.csv", "r") as f:
        stock_list = f.read().splitlines()
    
    #stock_list = ['GOV']
    
    # open the output file
    now = datetime.datetime.utcnow()
    filename = "c:\\py_scripts\\Scraper\\%s_DividendData.csv"%now.strftime("%Y%m%d_%H%M%S")
    csv_file = open(filename, "w")
    csv_file.write(DataScraper.HEADER)
    
    
    # build the data
    for ticker in stock_list:
        print ticker
        ds = DataScraper(ticker)
        csv_file.write(ds.drip_yield())

