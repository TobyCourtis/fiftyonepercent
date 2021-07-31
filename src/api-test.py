from binance.spot import Spot
import json
from notify.notify import slack_notify


def create_client():
    test = True
    with open("./keys/testnet-keys.json" if test else "./keys/default-keys.json") as json_data:
        keys = json.loads(json_data.read())
        API_KEY = keys["API_KEY"]
        API_SECRET = keys["API_SECRET"]

    client = Spot(key=API_KEY, secret=API_SECRET)
    return client


client = create_client()


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


def list_all(dict):
    for i in dict:
        print(f"{i}: {dict[i]}")


if (__name__ == "__main__"):
    avg_price()
