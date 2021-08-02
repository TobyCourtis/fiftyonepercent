from binance.error import ClientError
from binance.spot import Spot as Client
from main import list_all, account_info
import json
import os

# examples folder contains more request types
# https://github.com/binance/binance-connector-python/blob/master/examples
with open(os.path.dirname(__file__) +  "/../keys/testnet-keys.json") as json_data:
    keys = json.loads(json_data.read())
    TESTNET_API_KEY = keys["API_KEY"]
    TESTNET_API_SECRET = keys["API_SECRET"]

client = Client(TESTNET_API_KEY, TESTNET_API_SECRET, base_url="https://testnet.binance.vision")

params = {
    "symbol": "BTCUSDT",
    "side": "SELL",
    "type": "LIMIT",
    "timeInForce": "GTC",
    "quantity": 0.002,
    "price": 9500,
    "recvWindow": 60000
}

print("Order to sell BTC:")
try:
    response = client.new_order(**params)
    list_all(response)
except ClientError as error:
    print(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )

print("\nOrders:\n")
try:
    response = client.get_orders("BTCUSDT", recvWindow=60000)
    for i in response:
        print(i)
except ClientError as error:
    print(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )

account_info()