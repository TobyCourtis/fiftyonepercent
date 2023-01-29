import datetime as dt
import math
import os
import time
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np

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

epoch_to_minutes = lambda epoch: int(epoch_to_date(epoch)[-5:-3])

format_markdown = lambda markdown_table: "```\n" + markdown_table.to_markdown() + "\n```"

add_spacing = lambda text: f"\n{text}\n"


class Side(Enum):
    buy = 'BUY'
    sell = 'SELL'


class OrderType(Enum):
    limit = "LIMIT"
    limit_maker = "LIMIT_MAKER"
    market = "MARKET"
    stop_loss_limit = "STOP_LOSS_LIMIT"
    take_profit_limit = "TAKE_PROFIT_LIMIT"


def create_image_from_dataframe(df, file_path, name):
    fig_background_color = 'lightgrey'
    fig_border = 'black'

    plt.figure(linewidth=2,
               edgecolor=fig_border,
               facecolor=fig_background_color,
               tight_layout={'pad': 1},
               )
    rcolors = plt.cm.Oranges(np.full(len(df.index), 0.1))
    ccolors = plt.cm.Oranges(np.full(len(df.columns), 0.1))

    table = plt.table(cellText=df.values,
                      rowLabels=df.index,
                      colLabels=df.columns,
                      rowColours=rcolors,
                      colColours=ccolors,
                      loc='center')
    table.scale(1, 1.5)
    plt.suptitle(name)
    # Hide axes
    ax = plt.gca()
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.box(on=None)
    plt.draw()
    table.set_fontsize(11)

    footer_text = dt.datetime.today().strftime("%d-%b-%Y %HH:%MM")
    plt.figtext(0.95, 0.05, footer_text, horizontalalignment='right', size=6, weight='light')

    current_dir = os.path.dirname(os.path.realpath(__file__))
    fig = plt.gcf()
    plt.savefig(file_path,
                edgecolor=fig.get_edgecolor(),
                facecolor=fig.get_facecolor(),
                dpi=150
                )
    print(add_spacing(f"Saved image to {file_path}"))


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
