import yfinance as yf
from yfinance import ticker
import pandas as pd
import requests

# get s&p500 stock list 
payload=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
sp500_list = payload[0]
sp500_code = sp500_list['Symbol']


# download data from Yahoo
i = 0 
for ticker in sp500_code:
    data = yf.download(  # or pdr.get_data_yahoo(...
            # tickers list or string as well
            tickers = ticker,

            # use "period" instead of start/end
            # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # (optional, default is '1mo')
            period = "10y",

            # fetch data by interval (including intraday if period < 60 days)
            # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            # (optional, default is '1d')
            interval = "1d",

            # group by ticker (to access via data['SPY'])
            # (optional, default is 'column')
            group_by = 'ticker',

            # adjust all OHLC automatically
            # (optional, default is False)
            auto_adjust = True,

            # download pre/post regular market hours data
            # (optional, default is False)
            prepost = False,

            # use threads for mass downloading? (True/False/Integer)
            # (optional, default is True)
            threads = True,

            # proxy URL scheme use use when downloading?
            # (optional, default is None)
            proxy = None
        )

    # save data to csv file 
    file_path = '/Users/bowenduan/Applications/OneDrive/200_Knowledge/210_Academe/211_University/PACE University/105_Spring 2021/CS658 Analytics Capstone/CS668-2021/data/'
    data.to_csv(file_path+ticker+'.csv')
    i += 1
    print(f'{ticker} historial data download successfully, total {i} companies downloaded.')