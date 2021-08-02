from binance.error import ClientError
from binance.spot import Spot as Client
import json

# examples folder contains more request types
# https://github.com/binance/binance-connector-python/blob/master/examples
with open("../keys/testnet-keys.json") as json_data:
    keys = json.loads(json_data.read())
    TESTNET_API_KEY = keys["API_KEY"]
    TESTNET_API_SECRET = keys["API_SECRET"]

client = Client()
client = Client(TESTNET_API_KEY, TESTNET_API_SECRET, )

params = {
    "symbol": "BTCUSDT",
    "side": "SELL",
    "type": "LIMIT",
    "timeInForce": "GTC",
    "quantity": 0.002,
    "price": 9500,
}

try:
    response = client.new_order(**params)
    print(response)
except ClientError as error:
    print(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )

print("\nOrders:")
try:
    response = client.get_orders("BTCUSDT")
    for i in response:
        print(i)
except ClientError as error:
    print(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )
