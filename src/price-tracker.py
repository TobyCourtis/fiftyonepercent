from clients.binance import *
from notify.notify import *

MA = moving_average(get_klines())
cur_avg = float(avg_price())
if cur_avg > MA:
    print(f"ETH is up {cur_avg - MA}")
    google_mini_notify(f"ETH is up {cur_avg - MA}")
    slack_notify(f"ETH is up {cur_avg - MA}")
else:
    print(f"ETH is down {MA - cur_avg}")
    google_mini_notify(f"ETH is down {MA - cur_avg}")
    slack_notify(f"ETH is down {MA - cur_avg}")
