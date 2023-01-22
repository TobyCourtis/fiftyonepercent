import time

"""
HELPER FUNCTIONS

The opposite of Sam Stratton functions
"""


def moving_average(klines):
    """
    Moving Average of candlesticks
    :param klines: Candlesticks object
    :return: Moving Average of the candles within Candlesticks object
    """
    # take klines and get avg of each kline
    averages = []
    for i in klines["Close"]:  # TODO change to e.g (O + H + L + C)/4
        averages.append(float(i))
    # add all averages and divide by num klines
    return sum(averages) / len(averages)


# lamda to convert epoch (3 d.p) int to datetime string
epoch_to_date = lambda epoch: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(epoch) / 1000))
