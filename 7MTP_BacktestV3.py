'''

'''


from __future__ import (absolute_import, division, print_function,unicode_literals)

import datetime  
import os 
import backtrader as bt 
from backtrader.feeds import GenericCSVData 
import argparse

# better plotting and results analys
from backtrader_plotting import Bokeh
import pandas as pd
from joblib import dump, load



# extending orginal GenericCSVData to includes predict columns 
class GenericCSVDataEx(GenericCSVData):

    lines = (('predict'),)
    params = (('predict', 71),)
    
# creating strategy
maximum_holding = 5
class DPStrategy(bt.Strategy):
    params = (
        ('trailpercent', 0.05),
    )

    def __init__(self):
        # create list to store position
        self.hold_stocks = []
        self.log_data = []
        self.orders = {}
        
    def log(self, txt, dt=None):
        ''' logging function'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
        self.log_data.append(f'{dt.isoformat()} {txt}')
        
    def notify_order(self, order):
        if order.status in [bt.Order.Completed]:
            if order.isbuy():
                print(': BUY {} EXECUTED, Price: {:.2f}'.format( order.data._name, order.executed.price))
            else:  # Sell
                self.orders.pop(order.data._name)
                self.hold_stocks.remove(order.data._name)
                self.log(': SELL {} EXECUTED, Price: {:.2f}'.format( order.data._name, order.executed.price))
                # print('{}: SELL {} EXECUTED, Price: {:.2f}'.format(
                    # self.datetime.date(), order.data._name, order.executed.price))
        elif order.status in [bt.Order.Rejected, bt.Order.Margin, bt.Order.Cancelled, bt.Order.Expired]:
            if order.data._name in self.hold_stocks:
                self.hold_stocks.remove(order.data._name)
            self.log(': order {} Failed!'.format(order.data._name))
            # print('{}: order {} failed!'.format(self.datetime.date(), order.data._name))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(': TRADING {} OPERATION PROFIT, GROSS {:.2f}, NET {:.2f}'.format(
            trade.data._name, trade.pnl, trade.pnlcomm))
        #print('{}: TRADING {} OPERATION PROFIT, GROSS {:.2f}, NET {:.2f}'.format(
            #self.datetime.date(), trade.data._name, trade.pnl, trade.pnlcomm))
        
    def next(self):
        # print current postion situation
        self.log(f': Position: {self.hold_stocks}')
        # check if stock has been in selling order   
        for stk in self.hold_stocks:
    
            if stk not in self.orders:
                print(self.getdatabyname(stk)._name)
                self.orders[stk] = self.close(data = self.getdatabyname(stk),
                    exectype = bt.Order.StopTrail, trailpercent = self.p.trailpercent)

        if len(self.hold_stocks) < maximum_holding:
            buy_dict = {}
            # searching for the highest trading volume to buy
            for i, d in enumerate(self.datas):
                if d._name not in self.hold_stocks:
                    buy_dict[d] = self.datas[i].volume[0]
            buy_dict = sorted(buy_dict.items(), key = lambda x : x[1], reverse = True)
            for d in buy_dict:
                if (d[0]._name in self.hold_stocks) & (d[0].predict == 1):
                    continue
                
                # Set the buying share for each order
                stake = int(self.broker.cash / (maximum_holding - len(self.hold_stocks)) // (d[0].close[0])) 
                # stake = 100
                self.buy(data = d[0], size = stake)
                self.hold_stocks.append(d[0]._name)
                if len(self.hold_stocks) >= maximum_holding:
                    break
                
    def stop(self):
        with open('resluts_log.txt', 'w') as e:
            for line in self.log_data:
                e.write(line + '\n')


if __name__ == '__main__':
    #* Getting stock list 
    # getting currecnt working dirctory
    cwd = os.getcwd()
    path = cwd + '/TPData1'

    stocklist = []
    for filename in os.listdir(path):
        if filename.endswith('.csv'):
            stocklist.append(filename[3:-4])
    print(f'There are {len(stocklist)} stocks in S&P500 \n')

    cerebro = bt.Cerebro(stdstats=False)
    # adding strategy
    cerebro.addstrategy(DPStrategy)
    
    for stock in stocklist:
        datapath = cwd + f'/BTData1/bt_{stock}' +'.csv'
        # adding stock price data into backtesting system
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
        
        cerebro.adddata(data, name = stock)
       
    # set principle 
    cerebro.broker.setcash(100000.0)
    # set commission 
    cerebro.broker.setcommission(commission=0.00025)
    # Add analyzer
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name = 'SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DW')
    
 
    # print out starting capital 
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # start backtesting 
    results = cerebro.run()
    
    strat = results[0]
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('SR:', strat.analyzers.SharpeRatio.get_analysis())
    print('DW:', strat.analyzers.DW.get_analysis())

    # plot
    # cerebro.plot()
    #b = Bokeh(style='bar')
    #cerebro.plot(b)
    
    # print out final capital 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(f'return_rate: {round(cerebro.broker.getvalue()/100000 -1,4)*100}%')
    

