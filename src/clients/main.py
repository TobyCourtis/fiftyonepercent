import datetime
import json
import os

from binance.spot import Spot
from binance.error import ClientError

class BinanceClient:
    def __init__(self, **kwargs):
        if "test" in kwargs:
            test = kwargs["test"]
        else:
            test = True
        # allow usage globally
        self.test = test
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
        print(f"Initialised with test mode: {test}")

    def exchange_info(self):
        exchange_info = self.client.exchange_info()
        return exchange_info

    # Binance API utils

    def account_info(self):
        print("Account Info")
        acc_info = self.client.account(recvWindow=60000)  # TODO time sync and lower recvWindow
        for i in acc_info:
            if i == 'balances':
                print("balance:")
                for currency in acc_info[i]:
                    self.list_all(currency)
            else:
                print(f"{i}: {acc_info[i]}")

    def coin_info(self, symbol):
        coin_info = self.client.coin_info()
        for coin in coin_info:
            if coin["coin"] == symbol:
                print(f"\nETH balance: {coin['free']}")

    def avg_price(self):
        avg_price = self.client.avg_price("ETHGBP")
        self.list_all(avg_price)
        return avg_price["price"]

    def get_klines(self, timeframe, limit, **kwargs):  # hours, days
        timeNow = datetime.datetime.now().timestamp() * 1000
        startTime = (datetime.datetime.now() - datetime.timedelta(**kwargs)).timestamp() * 1000
        klines = self.client.klines("ETHGBP", timeframe, limit=limit, startTime=int(startTime), endTime=int(timeNow))
        labelledKlines = {
            "Open time": [x[0] for x in klines],
            "Open": [x[1] for x in klines],
            "High": [x[2] for x in klines],
            "Low": [x[3] for x in klines],
            "Close": [x[4] for x in klines],
            "Volume": [x[5] for x in klines],
            "Close time": [x[6] for x in klines],
            "Quote asset volume": [x[7] for x in klines],
            "Number of trades": [x[8] for x in klines],
            "Taker buy base asset volume": [x[9] for x in klines],
            "Taker buy quote asset volume": [x[10] for x in klines],
            "Ignore": [x[11] for x in klines],
        }
        return labelledKlines

    def ticker(self):
        print(self.client.ticker_price("ETHGBP"))

    def ticker_24h(self):
        print(self.client.ticker_24hr("ETHGBP"))

    def list_all(self, dict):
        for i in dict:
            print(f"{i}: {dict[i]}")

    # invest

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
            self.list_all(response)
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
        # TODO
        print("sell")

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

    # TA utils
    def moving_average(self, klines):
        # take klines and get avg of each kline
        averages = []
        for i in klines["Close"]:
            averages.append(float(i))
        # add all averages and divide by num klines
        return sum(averages) / len(averages)

    def kline_average(self, kline):
        # TODO change to e.g (O + H + L + C)/4
        return kline["Close"]  # could also take indexOf Close


if __name__ == "__main__":
    client = BinanceClient(test=True)
    client.show_orders("ETHUSDT")
