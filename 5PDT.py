'''
Apply the predition model trained to predict the price move direction for every company for every trading day in 2021
'''


from __future__ import (absolute_import, division, print_function,unicode_literals)

import datetime  
import os 
import backtrader as bt 
from backtrader.feeds import GenericCSVData 
import argparse

# better plotting and results analys
import pandas as pd
from joblib import load




#* Getting stock list 
# getting currecnt working dirctory
cwd = os.getcwd()
path = cwd + '/TPData1'

stocklist = []
for filename in os.listdir(path):
    if filename.endswith('.csv'):
        stocklist.append(filename[3:-4])
print(f'There are {len(stocklist)} stocks in S&P500 \n')

# predition on new data and assign position singal
# paper trading period: 20200208 ~ 20210208
#* Load Data
for filename in stocklist:
    filepath = f'{cwd}/LIData/li_{filename}.csv'
    df = pd.read_csv(f'{filepath}',index_col='Date')
    # df.set_index(['Date'])
    print(f'{filename} stock training data loaded. \n')
    print(f'{filename}Starting Prediction on backtesting date \n')
    df_trade = df[df.index > '2020-02-08'].drop('sgn', axis=1)

    #* load model
    model_name = os.path.join(f'{cwd}/Model1/',f'md_{filename}.joblib')
    model = load(model_name)
    df_trade['predict'] = model.predict(df_trade)
    # save prediction file 
    df_trade.to_csv(f'{cwd}/BTData1/bt_{filename}.csv')
    