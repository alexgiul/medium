import os
import pandas as pd

instrument = "SPY"
df = pd.read_csv(os.getcwd() + "/data/%s.csv" % instrument)   # load 20 years historical data

df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d')
df.set_index('timestamp', inplace=True)

df = df[['open', 'high', 'low', 'close', 'adjusted_close', 'volume']]

df.rename(columns={"open": "Open", "high": "High", "low": "Low", "adjusted_close": "Close", "volume": "Volume"}, inplace = True)

df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

#df = df[1500:]

df.sort_index(inplace=True)
#print(df.info())
print(df.tail())


import math
import backtrader as bt
import backtrader.feeds as btfeeds



class TrendFollower(bt.Strategy):
    '''This is a long-only strategy which operates on a moving average cross

    Entry rules:
        1. Go long  if:
            a. Current bar's close is greater than X-period moving average
        2. Close position if:
            a. Current bar's close is lower than X-period moving average


    Order Execution Type:
      - Market
    Notes:
    '''
    params = (
        ('printlog', True),
        ("period", 5)

    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))
            #logging.info('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            ep = order.executed.price
            es = order.executed.size
            tv = ep * es
            leverage = self.broker.getcommissioninfo(self.data).get_leverage()
            margin = abs((ep * es) / leverage)


            if order.isbuy():
                self.log(
                    '%s - BUY EXECUTED on %s, Price: %.2f, Size: %.2f, Comm %.2f, Margin %.2f' %
                    (self.data0._name,
                     order.info['name'],
                     order.executed.price,
                     order.executed.size,
                     order.executed.comm,
                     margin))

            else:  # Sell
                self.log(
                    '%s - SELL EXECUTED on %s, Price: %.2f, Size: %.2f, Comm %.2f, Margin %.2f' %
                    (self.data0._name,
                        order.info['name'],
                     order.executed.price,
                     order.executed.size,
                     order.executed.comm,
                     margin))

            # track all operation
            obj = (
                self.datas[0].datetime.date(0).isoformat(),
                "BUY" if order.isbuy() else "SELL",
                order.info['name'],
                order.executed.price,
                order.executed.value,
                order.executed.comm,
                order.size
            )
            #self.orders_tracking[self.datas[0].datetime.date(0).isoformat()] = obj

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f Account: %.2f' % (trade.pnl, trade.pnlcomm, self.broker.cash))
        #obj = self.orders_tracking[self.datas[0].datetime.date(0).isoformat()]
        #order_values = list(obj)
        #order_values.append(trade.ref)  # add the ref-id of trade so it is possible to link orders and trades
        #self.orders_tracking[self.datas[0].datetime.date(0).isoformat()] = tuple(order_values)
        #self.order_dict.clear()  # clean up stop loss/take profit prices


    def __init__(self):

        self.order = None
        # Add a ATR indicator for volatility measure
        self.atr = bt.indicators.ATR(self.datas[0], period=10)

        # Bollinger Bands
        # self.boll = bt.indicators.BollingerBands(period=self.p.period, devfactor=self.p.devfactor)

        # self.cross_down = bt.indicators.CrossDown(self.data.close, self.boll.lines.top)
        # self.cross_up = bt.indicators.CrossUp(self.data.close, self.boll.lines.bot)

        self.sma = bt.indicators.MovAv.SMA(period=self.p.period)
        self.sma200 = bt.indicators.MovAv.SMA(period=200)   # major trend filter

    def next(self):
        # Simply log the closing price of the series from the reference
        # print('Close, %.2f' % self.data.close)

        # uscita dalla posizione LONG
        if self.position.size>0:
            if self.data.close > self.sma:
                self.order = self.close() #sell(size=100)
                self.order.addinfo(name="Market Order")
                return

        # uscita dalla posizione SHORT
        if self.position.size<0:
            if self.data.close < self.sma:
                self.order = self.close() #sell(size=100)
                self.order.addinfo(name="Market Order")
                return


        # ingreso in posizione LONG
        if  self.atr[0] > self.atr[-10] and self.data.close < self.sma and self.data.close > self.sma200:
            order_size = 10000//self.data.close
            self.order = self.buy(size=order_size)
            self.order.addinfo(name="Market Order")
            return

        # ingreso in posizione SHORT
        if  self.atr[0] > self.atr[-10] and  self.data.close > self.sma and self.data.close < self.sma200:
            order_size = 10000//self.data.close
            self.order = self.sell(size=order_size)
            self.order.addinfo(name="Market Order")
            return


import numpy

datafeed = btfeeds.PandasData(dataname=df)

# Create an instance of cerebro
cerebro = bt.Cerebro(stdstats=True)
# Set our desired cash start
startcash = 100000
cerebro.broker.setcash(startcash)

# https://www.backtrader.com/docu/commission-schemes/commission-schemes/
# https://backtest-rookies.com/2017/09/26/backtrader-commission-schemes/
value_per_tick = 0.01  # value per tick see Trading Plan tables
decimal_digit_number = 2  # number of decimal digit after point
# cerebro.broker.setcommission(commission=2, margin=65,mult=value_per_tick / (10 ** -decimal_digit_number))
cerebro.broker.setcommission(commission=0.001)  # 1.8% of the operation value

# Analyzer
#cerebro.addanalyzer(analyzers.AcctStats, _name='as')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='ta')

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="mySharpe", riskfreerate=0.01, timeframe=bt.TimeFrame.Months)
cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="myReturn")
cerebro.addanalyzer(bt.analyzers.SQN, _name="mySqn")

# cerebro.addobserver(SLTPTracking)

# Add the strategy
cerebro.addstrategy(TrendFollower, printlog=True, period=5)

# Add the data to Cerebro
cerebro.adddata(datafeed, name=instrument)

#cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# Run over everything

cerebro.addobserver(bt.observers.Value)
strategies = cerebro.run()

#cerebro.plot(style='line')
# first_strategy = strategies[0]

# Get final portfolio Value
portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash

# Print out the final result
# print('Final Portfolio Value: ${}'.format(round(portvalue,2)))
print('P/L: ${}'.format(round(pnl, 2)))


analysis = strategies[0].analyzers.ta.get_analysis()

##################### SYSTEM REPORT ######################
trades_count = analysis['total']['closed']

print("                     %15s  %15s  %15s" % ( "All Trades", "Long Trades", "Short Trades"))
print("Total Net profit($): %15s  %15s  %15s" % ( round(analysis['pnl']['net']['total'],2),
                                             round(analysis['long']['pnl']['total'],2),
                                             round(analysis['short']['pnl']['total'],2)  ))

print('Trade #: {}'.format(trades_count))
print('Mean Trade: ${}'.format(round(pnl/trades_count, 2)))



print("Profit Factor:       %15s  %15s  %15s" % ( round(( -1 * analysis.won.pnl.total / analysis.lost.pnl.total),2),
                                                  round(( -1 * analysis.long.pnl.won.pnl.total / analysis.long.pnl.lost.pnl.total),2),
                                                  round(( -1 * analysis.short.pnl.won.pnl.total / analysis.short.pnl.lost.pnl.total),2)
                                                  ))
print("")