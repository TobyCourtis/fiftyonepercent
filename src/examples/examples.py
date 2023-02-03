"""
This file will house examples for using functions throughout our project

Examples will include buying, selling, plotting and more.
"""

import json

import pandas as pd

from src.clients.binance_client import BinanceClient
from src.clients.ma_crossover_utils import buy, sell
from src.utils.utils import Side, OrderType


def create_ma_crossover():
    client = BinanceClient(test=False)
    all_candles = client.get_klines(timeframe="1m", days=30)
    all_candles.create_crossover_graph(1, 2, units="days", save=False)


def test_create_ma_crossover():
    client = BinanceClient(test=True)
    all_candles = client.get_klines(timeframe="1m", days=1)
    all_candles.create_crossover_graph(1, 2, units="hours", save=False)


def _position_summary(test):
    client = BinanceClient(test=test)
    print(client.position_summary())


def _show_open_orders(test=True, filter=None):
    client = BinanceClient(test=test)
    client.show_open_orders(order_type_filter=filter, save_image=False)


def get_test_market_position():
    client = BinanceClient(test=True)
    print(client.get_market_position())


def get_prod_market_position():
    client = BinanceClient(test=False)
    print(client.get_market_position())


def place_limit_order(price):
    client = BinanceClient(test=False)
    client.place_limit_order(side=Side.buy, price=price)


def save_exchange_info():
    client = BinanceClient(test=True)

    filename = 'exchange_info'
    if client.test:
        filename += '_testnet'
    full_name = f'{filename}.json'
    with open(full_name, 'w', encoding='utf-8') as f:
        json.dump(client.exchange_info(), f, ensure_ascii=False, indent=4)
    print(f"Saved exchange info to ./{full_name}")


def average_price():
    client = BinanceClient(test=True)
    client.avg_price()


def _stop_order(stop_price):
    client = BinanceClient(test=True)
    client.place_stop_order(stop_price)  # if price goes to 500 sell


def _stop_order_prod(stop_price):
    client = BinanceClient(test=False)
    client.place_stop_order(stop_price)  # if price goes to 500 sell


def _cancel_all_open_orders_for_type(order_type):
    client = BinanceClient(test=True)
    client.cancel_all_open_orders_for_type(order_type)


def _coin_info_GBP():
    client = BinanceClient(test=False)
    print(client.coin_info("GBP"))


def _coin_info_ETH():
    client = BinanceClient(test=False)
    print(client.coin_info())


def dummy_dataframe():
    data = {'Close': [1595.1, 1595.2, 1595.3, 1595.4, 1595.5],
            'Short': [1593.1, 1593.2, 1593.3, 1593.4, 1593.5],
            'Long': [1594.3, 1594.2, 1594.1, 1592.1, 1592.2],
            'Signal': [0.0, 0.0, 0.0, 1.0, 1.0],
            'Position': [0.0, 0.0, 0.0, 1.0, 0.0]
            }

    index = ['2023-01-31 19:55:00', '2023-01-31 19:56:00', '2023-01-31 19:57:00', '2023-01-31 19:58:00',
             '2023-01-31 19:59:00']
    return pd.DataFrame(data, index=index)


def _ma_crossover_buy(test):
    ma_crossover_dataframe = dummy_dataframe()
    dummy_latest_row = ma_crossover_dataframe.iloc[-1]
    client = BinanceClient(test=test)
    buy(1, 2, "hours", dummy_latest_row, client)


def _ma_crossover_sell(test):
    ma_crossover_dataframe = dummy_dataframe()
    dummy_latest_row = ma_crossover_dataframe.iloc[-1]
    client = BinanceClient(test=test)
    sell(1, 2, "hours", dummy_latest_row, client)


def _account_balance_by_symbol(test, symbol=None, include_locked=False):
    client = BinanceClient(test=test)
    client.account_balance_by_symbol(symbol, include_locked)


def _all_account_info(test):
    client = BinanceClient(test=test)
    client.all_account_info()


def _get_account_balance_position_type(test):
    client = BinanceClient(test=test)
    print(client.get_account_balance_position_type())


def _market_sell_only():
    client = BinanceClient(test=False)
    client.market_order(Side.sell, 0.0151)


def _get_open_order_ids(test):
    client = BinanceClient(test=test)
    client.get_open_order_ids(order_type_filter=OrderType.stop_loss_limit)


if __name__ == "__main__":
    test = False
    _position_summary(test=test)
    # _account_balance_by_symbol(test=test, symbol="GBP")
    # _account_balance_by_symbol(test=test, symbol="ETH")
    # _account_balance_by_symbol(test=test, symbol="ETH", include_locked=True)
    # _ma_crossover_buy(test=test)
    # _ma_crossover_sell(test)

    # _get_open_order_ids(test=test)
