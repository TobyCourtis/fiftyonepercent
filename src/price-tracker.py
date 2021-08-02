from clients.main import *
from notify.notify import *
import sys


# price tracker
# first parameter must be hourly,daily,monthly

def notify_up(timeframe, change):
    msg = f"{timeframe}: Ethereum is up {round(change, 1)} percent "
    print(msg)
    google_mini_notify(msg)
    slack_notify(msg)


def notify_down(timeframe, change):
    msg = f"{timeframe}: Ethereum is down {round(change, 1)} percent."
    print(msg)
    google_mini_notify(msg)
    slack_notify(msg)


if sys.argv[1] == "daily":
    MA = moving_average(get_klines("15m", 8, days=1))
    perc_change = (float(avg_price()) / MA * 100) - 100
    if perc_change > 0:
        notify_up("Daily", perc_change)
    else:
        notify_down("Daily", perc_change)

elif sys.argv[1] == "hourly":
    MA = moving_average(get_klines("1m", 20, minutes=70))
    perc_change = (float(avg_price()) / MA * 100) - 100
    if perc_change > 0:
        notify_up("Hourly", perc_change)
    else:
        notify_down("Hourly", perc_change)
