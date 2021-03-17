
import pandas as pd
import os
from talib import abstract

#* Getting stock list 
# getting currecnt working dirctory
cwd = os.getcwd()
path = cwd + '/OData'

stocklist = []
for filename in os.listdir(path):
    if filename.endswith('.csv'):
        stocklist.append(filename[:-4])
print(f'There are {len(stocklist)} stocks in S&P500')



#* Prepare data
i = 0 
for filename in stocklist:
    try:
        #loading data
        # filename = 'A'
        df = pd.read_csv(f'{cwd}/OData/{filename}.csv')

        # label records
        # get the previouse day close to label the data
        df['NxtClose'] = df['Close'].shift(-1)
        # calculate the daily percent change
        df['Ptc'] = round(df['NxtClose']/df['Close'] - 1, 4)*100
        # 1 for price going up, 0 for price going down
        df['sgn'] = [1 if  x > 0 else 0 for x in df['Ptc']]
        print(df.head())

        # calculate variables
        # calculate ratios as machine learning variables 
        # these ratio calculation will be done by ta-lib
        # moving average 
        ma_list = [5, 10, 20, 30, 60]
        for i in ma_list:
            df[f'ma{i}'] = pd.Series(abstract.SMA(df, timeperiod = i,price = 'Close'), index = df.index)
        # volumne moving average     
        ma_vol_list = [5, 10, 20, 30, 60]
        for i in ma_vol_list:
            df[f'ma_vol{i}'] = pd.Series(abstract.SMA(df, timeperiod = i, price = 'Volume'), index = df.index)
        # add previouse 5 days data

        col = ['Close','ma5','ma10','ma20','ma30','ma60','ma_vol5','ma_vol10','ma_vol20','ma_vol30','ma_vol60']
        for j in col:
            for i in range(1,6):
                df[f'Pre{i}{j}'] = df[f'{j}'].shift(i)
                
        # clean data
        # reset index to datatime
        df = df.set_index(['Date'])
        # delet Next day close (future value) delet Ptc (future vale)
        df = df.drop(['NxtClose','Ptc'], axis= 1)
        # prepare training data
        df = df.dropna(axis=0)
        print(df.tail())
        df.to_csv(f'{cwd}/LIData/li_{filename}.csv')
        i = i + 1
        print(f'stock {filename} processed. total {i} stocks processed.')
        
    except Exception as ex: 
        print(ex)
