import math
import time

"""
HELPER FUNCTIONS

The opposite of Sam Stratton functions
"""


def moving_average(klines, limit=None):
    """
    Moving Average of candlesticks
    :param klines: Candlesticks object
    :return: Moving Average of the candles within Candlesticks object
    """
    close_prices = klines.close
    if limit is not None:
        close_prices = close_prices[:limit]

    # take klines and get avg of each kline
    averages = []
    for i in close_prices:  # TODO change to e.g (O + H + L + C)/4
        averages.append(float(i))
    # add all averages and divide by num klines
    return sum(averages) / len(averages)


def convert_to_hours(window_min, window_max, units):
    match units.lower():
        case "days":
            window_min = 24 * window_min
            window_max = 24 * window_max
        case "hours":
            pass  # already in hours
        case _:
            raise Exception(f"Unit '{units}' is not supported yet!")
    return window_min, window_max


# lamda to convert epoch (3 d.p) int to datetime string
# Important: Will round 14:03:59 > 14:04:00 for graph readability
epoch_to_date = lambda epoch: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(math.ceil(int(epoch) / 1000)))


def bruce_buffer():
    print(
        """
        |
        |
        |
        |
        |
        |
        |
        |
        |
        |
        |
        |
        """
    )
