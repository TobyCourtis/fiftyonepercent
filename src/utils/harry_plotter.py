import time

import plotly.graph_objects as go

from src.client.binance_client import BinanceClient
from src.client.candlesticks import Candlesticks


def plot(candles: Candlesticks):
    """
    Main plot function for any Candlesticks object

    NB:
    - Requires 3dp epoch openTime e.g. 1673708400000
    - Uses openTime for plots and not close

    :param candles: Input type of Candlesticks object
    :return: void function but plots a plotly graph in browser
    """
    fig = go.Figure(
        data=[go.Candlestick(x=[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x / 1000)) for x in candles.openTime],
                             open=candles.open,
                             high=candles.high,
                             low=candles.low,
                             close=candles.close)])

    fig.show()


if __name__ == "__main__":
    client = BinanceClient(test=True)
    candles = client.get_klines("15m", days=1)
    plot(candles)
