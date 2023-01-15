import plotly.graph_objects as go

from main import BinanceClient

import time

from candlesticks import Candlesticks


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
    foo = client.get_klines("15m", 8, days=1)
    plot(foo)
