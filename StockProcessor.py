
import scraper

import datetime
from collections import namedtuple

if __name__ == '__main__':
    # define the limits
    price_min = 2.00
    date_end = datetime.datetime(year=2018, month=2, day=28).date()
    rec_max = 2.0
    count_min = 5
    growth_min = 100.0
    market_cap_max = 1000.0
    
    now = datetime.datetime.utcnow()
    outname = "C:\\py_scripts\\Scraper\\%s_TargetStocks.csv"%now.strftime("%Y%m%d_%H%M%S")
    outfile = open(outname, "w")
    
    # add a header to the file
    outfile.write("Price Min($),%.2f\n"%price_min)
    outfile.write("End Date,%s\n"%date_end.strftime("%Y-%m-%d"))
    outfile.write("Max Mean Recommendation,%.1f\n"%rec_max)
    outfile.write("Minimum Recommendation Count,%d\n"%count_min)
    outfile.write("Minimum Growth(%%),%.1f\n"%growth_min)
    outfile.write("Maximum Market Cap($M),%.1f\n"%market_cap_max)
    outfile.write("\n")
    outfile.write(scraper.StockData.HEADER)
    outfile.write("\n")
    
    StockData = namedtuple("StockData", "ticker price drug indication phase date catalyst rec_mean sbuy buy count tlow tmean thigh tgrowth cap short")
    # open and read the file
    with open(r"C:\py_scripts\Scraper\20171016_034025_StockData.csv", "r") as f:
        for line in f:
            sd = StockData(*line.strip().split(","))
            
            # do we want this line?
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
    