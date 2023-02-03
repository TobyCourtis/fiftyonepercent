import sys

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


if __name__ == "__main__":
    binance_client = BinanceClient(test=False)
    if sys.argv[1] == "daily":
        MA = moving_average(binance_client.get_klines("15m", days=1),
                            limit=8)  # look at 2-hour period 1 day ago
        average_price = binance_client.avg_price()
        perc_change = (average_price / MA * 100) - 100
        if perc_change > 0:
            notify_up("Daily", perc_change, average_price)
        else:
            notify_down("Daily", perc_change, average_price)

    elif sys.argv[1] == "hourly":
        MA = moving_average(binance_client.get_klines("1m", minutes=70),
                            limit=20)  # look at 20-minute period 1h10m ago
        average_price = binance_client.avg_price()
        perc_change = (average_price / MA * 100) - 100

        if perc_change > 0:
            notify_up("Hourly", perc_change, average_price)
        else:
            notify_down("Hourly", perc_change, average_price)
