import datetime
import json
import os

from binance.spot import Spot


def create_client():
    test = True
    with open(os.path.dirname(__file__) + "/../keys/testnet-keys.json" if test else
              os.path.dirname(__file__) + "/../keys/default-keys.json") as json_data:
        keys = json.loads(json_data.read())
        API_KEY = keys["API_KEY"]
        API_SECRET = keys["API_SECRET"]

    client = Spot(key=API_KEY, secret=API_SECRET)
    return client


client = create_client()


# Binance API

def account_info():
    print("Account Info")
    account_info = client.account()
    for i in account_info:
        print(f"{i}: {account_info[i]}")


def coin_info(coinType):
    coin_info = client.coin_info()
    for coin in coin_info:
        if coin["coin"] == coinType:
            print(f"\nETH balance: {coin['free']}")


def exchange_info():
    exchange_info = client.exchange_info()
    print(exchange_info)


def avg_price():
    avg_price = client.avg_price("ETHGBP")
    list_all(avg_price)
    return avg_price["price"]


def get_klines(timeframe, limit, **kwargs):  # hours, days
    timeNow = datetime.datetime.now().timestamp() * 1000
    startTime = (datetime.datetime.now() - datetime.timedelta(**kwargs)).timestamp() * 1000
    klines = client.klines("ETHGBP", timeframe, limit=limit, startTime=int(startTime), endTime=int(timeNow))
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


def ticker():
    print(client.ticker_price("ETHGBP"))


def ticker_24h():
    print(client.ticker_24hr("ETHGBP"))


def list_all(dict):
    for i in dict:
        print(f"{i}: {dict[i]}")


# TA
def moving_average(klines):
    # take klines and get avg of each kline
    averages = []
    for i in klines["Close"]:
        averages.append(float(i))
    # add all averages and divide by num klines
    return sum(averages) / len(averages)


def kline_average(kline):
    # TODO change to e.g (O + H + L + C)/4
    return kline["Close"]  # could also take indexOf Close


if (__name__ == "__main__"):
    # print("MA: ", moving_average(get_klines()))
    print()
