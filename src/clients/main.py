import datetime
import json
import os

from binance.spot import Spot


def create_client():
    test = True
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

    return Spot(key=API_KEY, secret=API_SECRET, base_url=base_url)


client = create_client()


# Binance API utils

def account_info():
    print("Account Info")
    acc_info = client.account(recvWindow=60000)  # TODO time sync and lower recvWindow
    for i in acc_info:
        if i == 'balances':
            print("balance:")
            for currency in acc_info[i]:
                list_all(currency)
        else:
            print(f"{i}: {acc_info[i]}")


def coin_info(symbol):
    coin_info = client.coin_info()
    for coin in coin_info:
        if coin["coin"] == symbol:
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


# Binance Orders


# TA utils
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


if __name__ == "__main__":
    account_info()
