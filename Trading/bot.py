from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import talib
import datetime
import os.path
import sys

class GoldenCrossDeathCrossStrategy(bt.Strategy):
    params = (
        ("short_period", 50),  # Periodo de la media móvil corta
        ("long_period", 300),   # Periodo de la media móvil larga
    )

    def log(self, txt, dt= None):                       #Logging of the strategy
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.volume = self.data.volume
        self.rsi = bt.indicators.RSI(self.datas[0])

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                self.buyprice = order.executed.price 
                self.buycomm = order.executed.comm

            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                
            self.bar_executed = len(self)
        
        elif order.status in [order.Caceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % 
                 (trade.pnl, trade.pnlcomm))
        
    def next(self):

        self.log('Close, %.2f' % self.dataclose[0])

        if self.volume > self.volume[-1]:

            if not self.position:
                if self.rsi > 70 or (self.short_ma > self.long_ma and self.short_ma[-1] <= self.long_ma[-1]):
                    #Golden Cross
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                        
                    self.order = self.buy()
            else:
                if self.rsi < 20 or (self.short_ma < self.long_ma and self.short_ma[-1] >= self.long_ma[-1]):
                    #Death Cross
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])

                    self.order = self.sell()
        
##########################################################################

if __name__ == '__main__':

    cerebro = bt.Cerebro()      #broker instance created in the background

    cerebro.broker.setcommission(commission=0.001)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '../Trading/orcl-1995-2014.txt')

    data = bt.feeds.YahooFinanceCSVData(
        reverse = False,
        dataname = datapath,
        fromdate = datetime.datetime(1995, 1, 1),
        todate = datetime.datetime(2014, 1, 1),
    )

    cerebro.adddata(data)

    ####################################################################
    cerebro.addstrategy(GoldenCrossDeathCrossStrategy)

    cerebro.broker.setcash(100.0)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()