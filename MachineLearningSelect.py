'''
Selecting stock buy signal by machine learning 
Buy Signal: Machine Learning 
Sell Signal: close price < ma5
'''



from __future__ import (absolute_import, division, print_function,unicode_literals)
from threading import Condition
import tushare as ts
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from joblib import dump, load
from sklearn.utils import resample
from talib import abstract

import datetime  # 用于datetime对象操作
import os.path  # 用于管理路径
import sys  # 用于在argvTo[0]中找到脚本名称
import backtrader as bt # 引入backtrader框架
from backtrader.feeds import GenericCSVData # 用于扩展DataFeed
import pandas as pd

# better plotting and results analys
from backtrader_plotting import Bokeh

#* 1. download original data 
ts.set_token('a0f192a7b75e15dd2d8c16f0a300a6e2b055f55d1589cfef6eb2fa01') 
df = ts.pro_bar(ts_code='000001.SZ', adj='qfq', start_date='20150101', end_date='20210201')

col = ['trade_date','open','high','close','low','vol','pct_chg']
df = df[col].iloc[::-1]
print(df.head())
print(f'original data has been download. \n')

# add indicator 
# moving average 
ma_list = [5, 10, 20, 30, 60]
for i in ma_list:
    df[f'ma{i}'] = pd.Series(abstract.SMA(df, timeperiod = i), index = df.index)

# volumne moving average     
ma_vol_list = [5, 10, 20, 30, 60]
for i in ma_vol_list:
    df[f'ma_vol{i}'] = pd.Series(abstract.SMA(df, timeperiod = i, price = 'vol'), index = df.index)

# label data 
# if next day close price goes up, label as '1', otherwise as '0'
df['pct_chg_backward'] = df['pct_chg'].shift(-1)
df['sgn'] = [1 if x > 3 else 0 for x in df['pct_chg_backward']]

# save processed data
df_processed = df.drop(['pct_chg','pct_chg_backward'], axis=1).dropna(axis=0, how = 'any')
df_processed.to_csv('/Users/bowenduan/Applications/OneDrive/200_Knowledge/2150_MachineLearn/StockML/000001processed.csv')
print(f'data processing complete \n')
print(df_processed.head())

#* 2. prepare training data
# training period: 20150101 ~ 20190101
df_train = df_processed[df_processed['trade_date'] < '20190101' ]
# resample the training data 
sgn_1 = df_train[df_train['sgn'] == 1]
sgn_0 = df_train[df_train['sgn'] == 0]
len_1 = len(sgn_1)
len_0 = len(sgn_0)
print(f'Buying record has {len_1} row, while the other records have {len_0} row \n')

df_majority = sgn_0
df_minority = sgn_1

# Upsample minority class
df_minority_upsampled = resample(df_minority, 
                                 replace=True,     # sample with replacement
                                 n_samples= len_0,    # to match majority class
                                 random_state=42) # reproducible results
# Combine majority class with upsampled minority class
df_train = pd.concat([df_majority, df_minority_upsampled])
 
# Display new class counts
print('after resample, the records situation is: \n',df_train.sgn.value_counts())
df_train_x = df_train.drop(['trade_date','sgn'], axis=1)
df_train_y = df_train['sgn']
print(f'{len(df_train_x)} row training data is prepated.')

# testing period: 20190101 ~ 20200101
df_test = df_processed[(df_processed['trade_date'] > '20190101') & (df['trade_date'] < '20200101')]
df_test_x = df_test.drop(['trade_date','sgn'], axis=1)
df_test_y = df_test['sgn']
print(f'{len(df_test_x)} row test data is prepared. \n')


#* 2. train model
clf = RandomForestClassifier(max_depth=2, random_state=42)
clf_model = clf.fit(df_train_x,df_train_y)
df_test_predict =  clf_model.predict(df_test_x)
#save prediction results
df_test['predict'] = df_test_predict  
df_test.to_csv('000001_test_predict.csv')

#* 3. test model
print(f'classification reports \n')
print(confusion_matrix(df_test_y, df_test_predict))
print(f'Accuracy rate is {accuracy_score(df_test_y, df_test_predict)}')

#* 4. save model
dump(clf_model, '000001_model.joblib')
print('model saved')


#* 5. predition on new data and assign singal  
# refet to strategy py file
# paper trading period: 20200102 ~ 20210201
print('Starting Prediction on trading date')
df_trade = df_processed[df_processed['trade_date'] > '20200101'].drop('sgn', axis=1)
# load model
model = load('000001_model.joblib')
df_trade['predict'] = model.predict(df_trade.drop('trade_date', axis=1))
# save prediction file 
df_trade.to_csv('/Users/bowenduan/Applications/OneDrive/200_Knowledge/2150_MachineLearn/StockML/000001_prediction_sgn.csv', index=False)
print(df_trade[df_trade['predict'] == 1])


#* 6. backtesting

# single stock back testing
HOLD_STOCK_NUMBER = 3
# Extend DataFeed
class GenericCSVDataEx(GenericCSVData):
    # customize line
    lines = ('predict', 'ma5','ma30','ma_vol5','ma_vol30')
    params = (('predict', 16),('ma5',6),('ma30',9),('ma_vol5',11),('ma_vol30',14))

# creating a strategy
class DPStrategy(bt.Strategy):
    params = (
        ('trailpercent', 0.05),
    )
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datapredict = self.datas[0].predict
        self.datama5 = self.datas[0].ma5
        self.datama30 = self.datas[0].ma30
        self.datavol5 = self.datas[0].ma_vol5
        self.datavol30 = self.datas[0].ma_vol30
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.datapredict[0] == 1:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                # self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:
            Condition1 = self.datama5[0] < self.datama30[0]
            Condition2 = self.datavol5[0] > self.datavol30[0]

            if Condition1 & Condition2:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                # self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

if __name__ == '__main__':

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    #stklist = pd.read_csv(stkfilepath)['code'].tolist()

    cerebro = bt.Cerebro()
    # add strategy
    cerebro.addstrategy(DPStrategy)

    datapath = modpath + '/000001_prediction_sgn.csv'
    #add data
    data = GenericCSVDataEx(
            dataname = datapath,
            fromdate = datetime.datetime(2020, 1, 1),
            todate = datetime.datetime(2021, 2, 1),
            #todate = datetime.datetime(2018, 1, 15),
            nullvalue = 0.0,
            dtformat = ('%Y%m%d'),
            datetime = 0,
            open = 1,
            high = 2,
            low = 4,
            close = 3,
            volume = 5,
            openinterest = -1,
            predict = 16,
            ma5 = 6
            )
    cerebro.adddata(data, name = '000001.SZ')
    # set principle 
    cerebro.broker.setcash(50000.0)
    # set commission 
    cerebro.broker.setcommission(commission=0.00025)
    # set size 
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)
    # print out starting capital 
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # start backtesting 
    cerebro.run()
    #plot
    b = Bokeh(style='bar', plot_mode='single')
    cerebro.plot(b)
    # print out final capital 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())


 