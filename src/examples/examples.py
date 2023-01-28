"""
This file will house examples for using functions throughout our project

Examples will include buying, selling, plotting and more.
"""

from src.clients.binance_client import BinanceClient
from src.clients.helpers import Side


def plot_ma_crossover():
    client = BinanceClient(test=False)
    all_candles = client.get_klines(timeframe="1m", days=6)
    all_candles.plot_crossover(2, 4, units="days")


def place_testnet_market_order():
    client = BinanceClient(test=True)
    client.market_order("ETHUSDT", Side.sell, 1)
    print(client.position_risk())


if __name__ == "__main__":
    plot_ma_crossover()
