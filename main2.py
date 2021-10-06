import alpaca_trade_api as tradeapi
import numpy as np
import time
from config import *

class TradeAlgo:
    def __init__(self):
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self.symbol = 'SPY'
        self.lookback = 20
        self.ceiling, self.floor = 30, 10
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.9
        self.high = []
        self.close_prices = []
        self.highestPrice = 0
        self.breakoutlvl = 0
        self.qty = 10.0
        self.side = 'buy' 
        self.type = 'market'
        self.trail_price = None 
        self.time_in_force = 'gtc'
        


    def trade(self):
        if self.market_open:
            account = self.api.get_account()
            print(account.status)
            #dynamically determine the lookback length based on 30 day volatility
            barset = self.api.get_barset(self.symbol, 'day', limit=31)
            #Account for upper and lower limit of lookback length
            barset = self.api.get_barset(self.symbol, 'day', limit=31)
            price_bars = barset[self.symbol]
            data = price_bars._raw


            for closing_price in data:
                self.close_prices.append(closing_price['c'])

            todayvol = np.std(self.close_prices[1:31])
            yesterdayvol = np.std(self.close_prices[0:30])
            deltavol = (todayvol - yesterdayvol) / todayvol
            self.lookback = round(self.lookback * (1 + deltavol))

            print("lookback length",self.lookback)

            #account for the upper and lower limit of the lookback length
            if self.lookback > self.ceiling:
                self.lookback = self.ceiling

            elif self.lookback < self.floor:
                self.lookback = self.floor

            #List of daily high
            barset = self.api.get_barset(self.symbol, 'day', limit=self.lookback)
            _data = price_bars._raw

            for price in _data:
                self.high.append(price['h'])

            print("list of high prices", self.high)

            self.position = int(self.api.get_position(self.symbol).qty)

            print("position",self.position)

            #buy incase of a breakout
            if not self.position and close_prices[0] >= max(self.high[:-1]):
                self.submitOrder(self.symbol, self.qty, self.side, self.type, self.trail_price, self.time_in_force)
                self.breakoutlvl = max(self.high[:-1])
                self.highestPrice = self.breakoutlvl 

            #create trailing stop loss if invested
            if self.position:
            #if no order exits, send a stoploss
                if not self.api.list_orders(status='open'):
                    self.qty=self.position
                    self.side ='sell'
                    self.types='trailing_stop'
                    self.trail_price=(self.initialStopRisk * self.breakoutlvl)
                    
                    self.stopMarketTicket = self.submitOrder(self.symbol, self.qty, self.side, self.types, self.trail_price, self.time_in_force)

            #check if the asset's price is higher than highestPrice and trailing stop price not
            #  below initial stop price
            if self.close_prices[0] > self.highestPrice and (self.initialStopRisk * self.breakoutlvl) < (self.close_prices[0] * self.trailingStopRisk):

            #save the new high to highest price
                self.highestPrice = self.close_prices[0]

            #update the stop price/ trail_price
                self.trail_price = (self.close_prices[0] * self.trailingStopRisk)
                self.stopMarketTicket = self.submitOrder(self.symbol, self.qty, self.side, self.types, self.trail_price, self.time_in_force)
                print("updated stop price: ",trail_price)

        else:
            print("market closed")



    def submitOrder(self, symbol, qty, side, types, trail_price, time_in_force):
        if qty == 0:
           return

        print(f"submitting {side} order for {qty} of {symbol}")

        if trail_price is not None:
            order = self.api.submit_order(symbol, qty, side, types, trail_price, time_in_force)

        else:
            order = self.api.submit_order(symbol, qty, side, types, time_in_force)

        return order



    def market_open(self):
        clock = self.api.get_clock()
        return clock.is_open



algo = TradeAlgo()
algo.trade()
