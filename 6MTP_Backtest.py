from __future__ import (absolute_import, division, print_function,unicode_literals)

import datetime  
import os 
import backtrader as bt 
from backtrader.feeds import GenericCSVData 

# better plotting and results analys
from backtrader_plotting import Bokeh



# extending orginal GenericCSVData to includes predict columns 
class GenericCSVDataEx(GenericCSVData):

    lines = (('predict'),)
    params = (('predict', 72),)
    
# creating strategy
maximum_holding = 5
class DPStrategy(bt.Strategy):
    params = (
        ('trailpercent', 0.05),
    )
    def log(self, txt, dt=None):
        ''' loggibf function'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
    def __init__(self):
        # create list to store position
        self.hold_stocks = []
        self.orders = {}
        
    def notify_order(self, order):
        if order.status in [bt.Order.Completed]:
            if order.isbuy():
                print('{}: BUY {} EXECUTED, Price: {:.2f}'.format(self.datetime.date(), order.data._name, order.executed.price))
            else:  # Sell
                self.orders.pop(order.data._name)
                self.hold_stocks.remove(order.data._name)
                print('{}: SELL {} EXECUTED, Price: {:.2f}'.format(
                    self.datetime.date(), order.data._name, order.executed.price))
        elif order.status in [bt.Order.Rejected, bt.Order.Margin, bt.Order.Cancelled, bt.Order.Expired]:
            if order.data._name in self.hold_stocks:
                self.hold_stocks.remove(order.data._name)
            print('{}: order {} failed!'.format(self.datetime.date(), order.data._name))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        print('{}: TRADING {} OPERATION PROFIT, GROSS {:.2f}, NET {:.2f}'.format(
            self.datetime.date(), trade.data._name, trade.pnl, trade.pnlcomm))
        
    def next(self):
        # print current postion situation
        print(self.hold_stocks)
        
        # check if stock has been in selling order   
        for stk in self.hold_stocks:
    
            if stk not in self.orders:
                print(self.getdatabyname(stk)._name)
                self.orders[stk] = self.close(data = self.getdatabyname(stk),
                    exectype = bt.Order.StopTrail, trailamount = 0, trailpercent = self.p.trailpercent)

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
                stake = int(self.broker.cash / (maximum_holding - len(self.hold_stocks)) // (d[0].close[0] * 100)) * 100
                self.hold_stocks.append(d[0]._name)
                self.buy(data = d[0], size = stake)
                if len(self.hold_stocks) >= maximum_holding:
                    break


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
    
    cerebro = bt.Cerebro()
    # adding strategy
    cerebro.addstrategy(DPStrategy)
    
    for stock in stocklist:
        datapath = path + f'/tp_{stock}' +'.csv'
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
                predict = 72,
                ma5 = 6
                )
        
        cerebro.adddata(data, name = stock)
       
    # set principle 
    cerebro.broker.setcash(100000.0)
    # set commission 
    cerebro.broker.setcommission(commission=0.00025)
    # print out starting capital 
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # start backtesting 
    cerebro.run()

    # plot
    # cerebro.plot()
    # b = Bokeh(style='bar')
    # cerebro.plot(b)
    
    # print out final capital 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(f'return_rate: {round(cerebro.broker.getvalue()/100000 -1,4)*100}%')

