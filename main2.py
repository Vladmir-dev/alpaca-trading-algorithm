import alpaca_trade_api as tradeapi
import numpy as np
import time
from time import sleep
from config import *

class TradeAlgo:
    def __init__(self):
        self.api = tradeapi.REST(api_key, api_secret, base_url)
        self.symbol = 'QQQ'
        self.lookback = 20
        self.ceiling, self.floor = 30, 10
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.9
        self.high = []
        self.close_prices = []
        self.highestPrice = 0
        self.breakoutlvl = None
        self.qty = 10
        self.side = 'buy' 
        self.type = 'market'
        self.trail_price= ''
        self.time_in_force = 'gtc'
        


    def trade(self, symbol):
        if self.market_open:
            account = self.api.get_account()
            print(account.status)
            #dynamically determine the lookback length based on 30 day volatility
            barset = self.api.get_barset(self.symbol, 'day', limit=31)
            #Account for upper and lower limit of lookback length
            # barset = self.api.get_barset(self.symbol, 'day', limit=31)
            price_bars = barset[self.symbol]
            data = price_bars._raw
            

            # self.close_prices = [closing_price['c'] for closing_price in data]

            for closing_price in data:
                self.close_prices.append(closing_price['c'])
            
            print("closing prices", self.close_prices)

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

            # self.high = [price for price in _data if data['h]]
            for price in _data:
                self.high.append(price['h'])

            print("list of high prices", self.high)
            # print("maximum price", max(self.high))

            self.position = int(self.api.get_position(self.symbol).qty)

            print("position",self.position)

             # First, get an up-to-date price for our symbol
            symbol_bars = self.api.get_barset(self.symbol, 'minute', 1).df.iloc[0]
            symbol_close_price = symbol_bars[self.symbol]['close']
            print("latest symbol price",symbol_close_price)

            #buy incase of a breakout
            if not self.position and symbol_close_price >= max(self.high):
                # self.submitOrder(self.symbol, self.qty, self.side, self.type, self.trail_price, self.time_in_force)
                order = self.api.submit_order(symbol=self.symbol, qty=self.qty, side=self.side, type=self.type, time_in_force=self.time_in_force)
                print(f"submitting {self.side} order for {self.qty} of {self.symbol}")

                if self.breakoutlvl is None:
                    self.breakoutlvl = max(self.high)
                self.highestPrice = self.breakoutlvl 
            
            else:
                if self.breakoutlvl is None:
                    self.breakoutlvl = max(self.high)
                self.highestPrice = self.breakoutlvl


            print("breakout level", self.breakoutlvl)

            #create trailing stop loss if invested
            if self.position:
            #if no order exits, send a stoploss
                if not self.api.list_orders(status='open'):
                    self.qty=self.position
                    self.side ='sell'
                    self.type='trailing_stop'
                    self.trail_price = self.initialStopRisk * self.breakoutlvl
                    self.trail_price = ((self.trail_price * 25)/100)-5
                    # self.trail_price = str(trail_price)
                    print("trail price ", self.trail_price)

                    self.stopMarketTicket = self.api.submit_order(symbol=self.symbol, 
                    qty=self.qty, 
                    side=self.side, 
                    type=self.type, 
                    trail_price=self.trail_price, 
                    time_in_force=self.time_in_force
                    )
                    
                    print(f"submitting {self.side} order for {self.qty} of {self.symbol}")
            #check if the asset's price is higher than highestPrice and trailing stop price not
            #  below initial stop price
            if symbol_close_price > self.highestPrice and (self.initialStopRisk * self.breakoutlvl) < (symbol_close_price * self.trailingStopRisk):

            #save the new high to highest price
                self.highestPrice = symbol_close_price

            #update the stop price/ trail_price
                self.trail_price = (symbol_close_price * self.trailingStopRisk)
                self.stopMarketTicket = self.api.submit_order(symbol=self.symbol, qty=self.qty, side=self.side, type=self.type, trail_price=self.trail_price, time_in_force=self.time_in_force)
                print(f"submitting {self.side} order for {self.qty} of {self.symbol}")
                print("updated stop price: ",self.trail_price)

        else:
            self.wait_for_market_open()
            self.trade()



    def market_open(self):
        clock = self.api.get_clock()
        return clock.is_open



    def wait_for_market_open(self):
        clock = self.api.get_clock()

        if not clock.is_open:
            time_to_open = (clock.is_open - clock.timestamp).total_seconds()
            sleep(time_to_open)
            print("market is open......")


    # def order_updates(self):
    #     conn = tradeapi.stream2.StreamConn()
    #     client_order_id = r'my_client_order_id'


algo = TradeAlgo()
algo.trade()
