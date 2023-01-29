"""
This file will house examples for using functions throughout our project

Examples will include buying, selling, plotting and more.
"""

import json

from src.clients.binance_client import BinanceClient
from src.clients.helpers import Side


def create_ma_crossover():
    client = BinanceClient(test=False)
    all_candles = client.get_klines(timeframe="1m", days=30)
    all_candles.create_crossover_graph(1, 2, units="days", save=False)


def place_testnet_market_order():
    client = BinanceClient(test=True)
    client.market_order("ETHUSDT", Side.sell, 1)
    print(client.position_summary())


def report_summary_position_risk():
    client = BinanceClient(test=True)
    print(client.position_summary())


def get_live_orders(filter=None):
    client = BinanceClient(test=True)
    print(client.show_open_orders(order_type_filter=filter))


def get_test_market_position():
    client = BinanceClient(test=True)
    print(client.get_market_position())


def remove_all_stop_orders_():
    client = BinanceClient(test=True)
    client.remove_all_stop_orders()


def place_limit_order():
    client = BinanceClient(test=True)
    client.place_limit_order(side=Side.buy, price=500)


def save_exchange_info():
    client = BinanceClient(test=True)

    filename = 'exchange_info'
    if client.test:
        filename += '_testnet'
    full_name = f'{filename}.json'
    with open(full_name, 'w', encoding='utf-8') as f:
        json.dump(client.exchange_info(), f, ensure_ascii=False, indent=4)
    print(f"Saved exchange info to ./{full_name}")


if __name__ == "__main__":
    # average_price()
    # place_limit_order(price=500)
    # remove_all_stop_orders_()
    get_live_orders(OrderType.limit)
    # report_summary_position_risk()
