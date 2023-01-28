"""
This file will house examples for using functions throughout our project

Examples will include buying, selling, plotting and more.
"""

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


if __name__ == "__main__":
    create_ma_crossover()
