import sys
from pathlib import Path

import requests

root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from notify import notifier
from src.client.binance_client import BinanceClient
from src.utils.utils import moving_average


# first argument must be hourly OR daily

def notify_up(timeframe, change, avg_price):
    msg = f"{timeframe}: Ethereum is up {round(change, 1)} percent at {round(avg_price, 1)}"
    print(msg)
    # google_mini_notify(msg)
    notifier.slack_notify(msg, channel='crypto-trading')


def notify_down(timeframe, change, avg_price):
    msg = f"{timeframe}: Ethereum is down {round(change, 1)} percent at {round(avg_price, 1)}"
    print(msg)
    # google_mini_notify(msg)
    notifier.slack_notify(msg, channel='crypto-trading')


def get_usd_to_gbp_exchange_rate():
    endpoint = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/gbp.json"

    response = requests.get(endpoint)
    data = response.json()

    exchange_rate = data['gbp']['usd']
    return float(exchange_rate)


def convert_usd_to_gbp(original_price, exchange_rate):
    return round(original_price / exchange_rate, 2)


if __name__ == "__main__":
    cur_exchange_rate = get_usd_to_gbp_exchange_rate()
    binance_client = BinanceClient(test=False)
    if sys.argv[1] == "daily":
        MA = moving_average(binance_client.get_klines("15m", days=1),
                            limit=8)  # look at 2-hour period 1 day ago
        MA = convert_usd_to_gbp(MA, cur_exchange_rate)
        average_price = binance_client.avg_price()
        average_price = convert_usd_to_gbp(average_price, cur_exchange_rate)

        perc_change = (average_price / MA * 100) - 100
        if perc_change > 0:
            notify_up("Daily", perc_change, average_price)
        else:
            notify_down("Daily", perc_change, average_price)

    elif sys.argv[1] == "hourly":
        MA = moving_average(binance_client.get_klines("1m", minutes=70),
                            limit=20)  # look at 20-minute period 1h10m ago
        MA = convert_usd_to_gbp(MA, cur_exchange_rate)
        average_price = binance_client.avg_price()
        average_price = convert_usd_to_gbp(average_price, cur_exchange_rate)
        perc_change = (average_price / MA * 100) - 100

        if perc_change > 0:
            notify_up("Hourly", perc_change, average_price)
        else:
            notify_down("Hourly", perc_change, average_price)
