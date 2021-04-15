from __future__ import (absolute_import, division, print_function,unicode_literals)
import pandas as pd
from joblib import dump, load
from sklearn.utils import resample
from talib import abstract

import datetime  #
import os 
import sys  
import backtrader as bt 
from backtrader.feeds import GenericCSVData
import pandas as pd

# better plotting and results analys
from backtrader_plotting import Bokeh

#* Getting stock list 
# getting currecnt working dirctory
cwd = os.getcwd()
path = cwd + '/TPData'

stocklist = []
for filename in os.listdir(path):
    if filename.endswith('.csv'):
        stocklist.append(filename[3:-4])
print(f'There are {len(stocklist)} stocks in S&P500 \n')

# predition on new data and assign position singal
# paper trading period: 20200208 ~ 20210208
#* Load Data
filename = 'A'
cwd = os.getcwd()
filepath = f'{cwd}/LIData/li_{filename}.csv'
df = pd.read_csv(f'{filepath}',index_col='Date')
# df.set_index(['Date'])
print(f'{filename} stock training data loaded.')
print(df.head())
print('Starting Prediction on backtesting date')
df_trade = df[df.index > '2020-02-08'].drop('sgn', axis=1)


#* load model
model_name = os.path.join(f'{cwd}/Model/',f'md_{filename}.joblib')
model = load(model_name)
df_trade['predict'] = model.predict(df_trade)
# save prediction file 
df_trade.to_csv(f'{cwd}/BTData/bt_{filename}.csv')


#* Create Strategy
class GenericCSVDataEx(GenericCSVData):
    # customize line
    lines = ('predict', 'ma5','ma30','ma_vol5','ma_vol30')
    params = (('predict', 71),('ma5',6),('ma30',9),('ma_vol5',11),('ma_vol30',14))

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

            # not postion then buy when condiction satisfied
            if self.datapredict[0] == 1:
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

    modpath = os.getcwd()

    #stklist = pd.read_csv(stkfilepath)['code'].tolist()

    cerebro = bt.Cerebro()
    # add strategy
    cerebro.addstrategy(DPStrategy)

    datapath = modpath + f'/BTData/bt_{filename}.csv'
    #add data
    data = GenericCSVDataEx(
            dataname = datapath,
            fromdate = datetime.datetime(2020, 1, 1),
            todate = datetime.datetime(2021, 2, 20),
            #todate = datetime.datetime(2018, 1, 15),
            nullvalue = 0.0,
            dtformat = ('%Y-%m-%d'),
            datetime = 0,
            open = 1,
            high = 2,
            low = 3,
            close = 4,
            volume = 5,
            openinterest = -1,
            predict = 71,
            ma5 = 6
            )
    cerebro.adddata(data, name = 'AAPL')
    # set principle 
    cerebro.broker.setcash(100000.0)
    # set commission 
    cerebro.broker.setcommission(commission=0.00025)
    # set size 
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    # print out starting capital 
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # start backtesting 
    cerebro.run()

    #plot
    b = Bokeh(style='bar', plot_mode='single')
    cerebro.plot(b)
    
    # print out final capital 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(f'return_rate: {round(cerebro.broker.getvalue()/100000 -1,4)*100}%')