import datetime
import json
import os
from pprint import pprint

from binance.error import ClientError
from binance.spot import Spot

from candlesticks import Candlesticks


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
            input("\nYou are in production mode. Press any key to continue\n")

            key_path = os.path.dirname(__file__) + "/../keys/default-keys.json"
            base_url = "https://api.binance.com"

        with open(key_path) as json_data:
            keys = json.loads(json_data.read())
            API_KEY = keys["API_KEY"]
            API_SECRET = keys["API_SECRET"]

        self.client = Spot(key=API_KEY, secret=API_SECRET, base_url=base_url)
        print(f"Initialised with test mode: {test}")

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

    def ticker_price(self):
        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now
        print(self.client.ticker_price(symbol=symbol))

    def get_klines(self, timeframe, limit, **kwargs) -> Candlesticks:
        """
        This is the main marketplace data return function

        :param timeframe: the interval of candlestick, e.g 1s, 1m, 5m, 1h, 1d, etc.
        :param limit: limit the no. candles returned Default 500; max 1000.
        :param kwargs: period of time to begin candles from time now minus,  e.g days=1, hours=0, weeks=0, minutes=0
        :return: Candlesticks object. Containing list of candles.
        """
        timeNow = datetime.datetime.now().timestamp() * 1000
        startTime = (datetime.datetime.now() - datetime.timedelta(**kwargs)).timestamp() * 1000

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now
        klines = self.client.klines(interval=timeframe,
                                    limit=limit,
                                    symbol=symbol,
                                    startTime=int(startTime),
                                    endTime=int(timeNow))

        all_candles = Candlesticks()
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

    def buy(self, symbol):
        if not self.test:
            print("Buying is disabled outside of test mode")
            exit()

        params = {
            "symbol": symbol,
            "side": "SELL",
            "type": "LIMIT",
            "timeInForce": "GTC",  # TODO - What is this enum
            "quantity": 0.002,
            "price": 9500,  # TODO - Look at docs for why price is specified
            "recvWindow": 60000
        }

        print(f"Order to sell {symbol}:")
        try:
            response = self.client.new_order(**params)
            pprint(response)
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    def sell(self):
        if not self.test:
            print("Selling is disabled outside of test mode")
            exit()
        # TODO implement sell
        print("sell")


if __name__ == "__main__":
    client = BinanceClient(test=False)
    all_candles = client.get_klines(timeframe="1h", limit=1000, days=30)
    all_candles.plot_crossover(1, 2, units="days")

    print("Finished and exited")
