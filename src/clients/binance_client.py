import datetime
import datetime as dt
import json
import os
from pprint import pprint

import numpy as np
import pandas as pd
from binance.error import ClientError
from binance.spot import Spot

from src.clients.candlesticks import Candlesticks
from src.clients.helpers import Side
from src.notify.notifier import slack_notify


class BinanceClient:
    def __init__(self, **kwargs):
        if "test" in kwargs:
            test = kwargs["test"]
        else:
            test = True

        self.test = test  # allow usage globally

        if test:
            key_path = os.path.dirname(__file__) + "/../keys/testnet-keys.json"
            base_url = "https://testnet.binance.vision"
        else:
            key_path = os.path.dirname(__file__) + "/../keys/default-keys.json"
            base_url = "https://api.binance.com"

        with open(key_path) as json_data:
            keys = json.loads(json_data.read())
            API_KEY = keys["API_KEY"]
            API_SECRET = keys["API_SECRET"]

        self.client = Spot(key=API_KEY, secret=API_SECRET, base_url=base_url)
        print(f"Initialised BinanceClient with test mode: {test}")

    """
    MISC
    """

    def exchange_info(self):
        """
        Current exchange trading rules and symbol information
        :return: Large dictionary of exchange information
        """
        exchange_info = self.client.exchange_info()
        return exchange_info

    """
    ACCOUNT INFORMATION
    """

    def account_info(self):
        print("Account Info")
        acc_info = self.client.account(recvWindow=60000)  # TODO time sync and lower recvWindow
        for i in acc_info:
            if i == 'balances':
                print("balance:")
                for currency in acc_info[i]:
                    pprint(currency)
            else:
                print(f"{i}: {acc_info[i]}")

    def show_orders(self, symbol):
        try:
            response = self.client.get_orders(symbol, recvWindow=60000)
            if len(response) == 0:
                print("No orders were found")
                return
            for i in response:
                print(i)
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    """
    POSITION/PNL INFORMATION
    """

    def position_risk(self, symbol_list=["ETHUSDT"]):
        """

        Function to return the position and PnL of each coin holding

        :param symbol_list: list of coins that you want included in the report
        :return: Dataframe showing the coins in the index and pnl in the columns. DF will include WAP.
        """

        pnl_df = []
        for symbol in symbol_list:
            trade_history = self.client.my_trades(symbol=symbol)
            live_px = float(self.client.ticker_price(symbol=symbol)['price'])
            symbol_data = []
            for trade_info in trade_history:
                coin_data = {}
                coin_data['Symbol'] = trade_info['symbol']
                coin_data['qty'] = float(trade_info['qty']) if trade_info['isBuyer'] == True else float(
                    trade_info['qty']) * -1
                coin_data['WAP'] = float(trade_info['price']) * float(trade_info['qty'])
                coin_data['Fee'] = float(trade_info['commission'])
                coin_data['Side'] = 'Buy' if trade_info['isBuyer'] == True else 'Sell'  # 1 is buy and 0 Sell
                coin_data['PnL'] = ((live_px - float(trade_info['price'])) * float(coin_data['qty'])) - float(
                    trade_info['commission'])
                symbol_data.append(coin_data)
            symbol_data = pd.DataFrame(symbol_data)
            symbol_data = symbol_data.groupby(['Symbol', 'Side']).sum()
            symbol_data['WAP'] = abs(symbol_data['WAP'] / symbol_data['qty'])
            symbol_data.reset_index(inplace=True)
            total_df = pd.DataFrame(
                [symbol, 'Total', symbol_data.qty.sum(), np.nan, symbol_data.Fee.sum(), symbol_data.PnL.sum()],
                index=symbol_data.columns).T

            symbol_data = symbol_data.append(total_df)
            pnl_df.append(symbol_data)

        pnl_df = pd.concat(pnl_df, axis=1)
        return pnl_df

    """
    MARKET INFORMATION
    """

    def coin_info(self, symbol):
        coin_info = self.client.coin_info()
        for coin in coin_info:
            if coin["coin"] == symbol:
                print(f"\nETH balance: {coin['free']}")

    def avg_price(self):
        avg_price = self.client.avg_price("ETHGBP")
        pprint(avg_price)
        return avg_price["price"]

    def ticker_price(self, symbol="ETHUSDT"):
        print(self.client.ticker_price(symbol=symbol))

    def get_klines(self, timeframe="1m", **kwargs) -> Candlesticks:
        """
        This is the main marketplace data return function

        :param timeframe: the interval of candlestick, e.g 1s, 1m, 5m, 1h, 1d, etc.
        :param kwargs: period of time to begin candles from time now minus,  e.g days=1, hours=0, weeks=0, minutes=0
        :return: Candlesticks object. Containing list of candles.
        """
        timeNow = datetime.datetime.now().timestamp() * 1000
        if "startTime" in kwargs:
            startTime = kwargs['startTime']
        else:
            startTime = (datetime.datetime.now() - datetime.timedelta(**kwargs)).timestamp() * 1000

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        gathered_all_klines = False
        all_candles = Candlesticks()
        all_candles.candleTimeframe = timeframe

        call_count = 1
        while not gathered_all_klines:
            print(f"Candle API call count: {call_count}")
            call_count += 1

            klines = self.client.klines(interval=timeframe,
                                        limit=1000,
                                        symbol=symbol,
                                        startTime=int(startTime),
                                        endTime=int(timeNow))

            for kline in klines:
                all_candles.openTime.append(kline[0])
                all_candles.open.append(kline[1])
                all_candles.high.append(kline[2])
                all_candles.low.append(kline[3])
                all_candles.close.append(kline[4])
                all_candles.volume.append(kline[5])
                all_candles.closeTime.append(kline[6])
                all_candles.quoteAssetVolume.append(kline[7])
                all_candles.numberOfTrades.append(kline[8])
                all_candles.takerBuyBaseAssetVolume.append(kline[9])
                all_candles.takerBuyQuoteAssetVolume.append(kline[10])
                all_candles.ignore.append(kline[11])

            # check if API response limit met
            if len(klines) < 1000:
                gathered_all_klines = True
            else:
                startTime = all_candles.closeTime[-1]  # renew data pull from latest candle close time
        return all_candles

    def ticker_24h(self):
        """
        24hr Ticker Price Change Statistics for symbol (for now only ETH)
        :return: 24hour rolling window price change statistics.
        """
        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now
        return self.client.ticker_24hr(symbol)

    """
    TRADE FUNCTIONS
    """

    def market_order(self, symbol, side: Side, qty: float):

        if not self.test:
            print("Buying is disabled outside of test mode")
            exit()

        if not isinstance(side, Side):
            raise TypeError('Side must be Equal to BUY or SELL')

        params = {
            "symbol": symbol,
            "side": side.value,
            "type": "MARKET",
            "quantity": str(qty),
            "timestamp": int(round(dt.datetime.today().timestamp()))
        }

        print(f"Order to {side.value} {symbol}:")

        try:
            response = self.client.new_order(**params)
            fills = response['fills']
            qty = 0
            wap = 0
            for fill in fills:
                wap += float(fill['qty']) * float(fill['price'])
                qty += float(fill['qty'])
            wap = wap / qty
            order_message = "Order filled - qty: %s price: %s" % (round(qty, 2), round(wap, 2))
            slack_notify(order_message, "crypto-trading")
            return order_message
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )


if __name__ == "__main__":
    client = BinanceClient(test=True)
    client.market_order("ETHUSDT", Side.sell, 1)
    print(client.position_risk())

    print("Finished and exited")
