from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from helpers import epoch_to_date


class Candlesticks:
    """
    NB: This data type stores many and not singular candlesticks

    Candlestick type derived from API: https://binance-docs.github.io/apidocs/#kline-candlestick-data
    """

    def __init__(self, **kwargs):
        self.openTime = []  # epoch time with 3 d.p
        self.open = []
        self.high = []
        self.low = []
        self.close = []
        self.volume = []
        self.closeTime = []  # epoch time with 3 d.p
        self.quoteAssetVolume = []
        self.numberOfTrades = []
        self.takerBuyBaseAssetVolume = []
        self.takerBuyQuoteAssetVolume = []
        self.ignore = []

        self.timeframe = "NONE"

    def display_all_candle_data(self):
        pprint(vars(self))

    def minute_conversion_factor(self):
        match self.timeframe[-1]:
            case "m":
                amount = int(self.timeframe[:-1])
                return int(60 / amount)
            case "d":
                return 1
            case "h":
                return 1
            case _:
                raise Exception(f"Timeframe '{self.timeframe}' is not supported yet!")

    def plot_crossover(self, window_min, window_max, units="days"):
        """
        Main function used to plot the MA crossover

        :param window_min:  Short window size
        :param window_max:  Long window size
        :param units: units of window_min/max in days or hours
        :return: (void) Plots the MA crossover graph
        """
        main_df = pd.DataFrame(self.close, columns=['Close'])
        df_close_time = pd.DataFrame(self.closeTime, columns=['CloseTime'])

        minute_conversion_factor = self.minute_conversion_factor()

        match units.lower():
            case "days":
                conversion_factor = 24 * minute_conversion_factor  # 24h * 60 minutes (to match candle size in minutes)
            case "hours":
                conversion_factor = 1 * minute_conversion_factor  # 1h * 60 minutes
            case _:
                raise Exception(f"Unit '{units}' is not supported yet!")

        window_min = window_min * conversion_factor
        window_max = window_max * conversion_factor

        main_df['Short'] = main_df['Close'].rolling(window=window_min).mean()
        main_df['Long'] = main_df['Close'].rolling(window=window_max).mean()

        main_df.index = df_close_time['CloseTime'].apply(epoch_to_date)

        main_df['Signal'] = np.where(main_df['Short'] > main_df['Long'], 1.0, 0.0)
        main_df['Position'] = main_df['Signal'].diff()

        main_df.dropna(inplace=True)
        main_df = main_df.astype(float)

        # PLOT
        plt.figure(figsize=(20, 10))

        main_df['Close'].plot(color='k', label='Close Price')
        main_df['Short'].plot(color='b', label='Short Price')
        main_df['Long'].plot(color='g', label='Long Price')

        # plot 'buy' signals
        main_df['buy_sell_x'] = main_df['Position'].replace(0.0, np.NAN)
        main_df['buy_y'] = main_df.apply(lambda x: x['Short'] if x['buy_sell_x'] == 1.0 else np.NAN, axis=1)
        main_df['sell_y'] = main_df.apply(lambda x: x['Long'] if x['buy_sell_x'] == -1.0 else np.NAN, axis=1)

        plt.plot(main_df['buy_sell_x'].index,
                 main_df['buy_y'],
                 '^', markersize=15, color='g', label='buy')

        # plot 'sell' signals
        plt.plot(main_df['buy_sell_x'].index,
                 main_df['sell_y'],
                 'v', markersize=15, color='r', label='sell')

        # METADATA
        plt.ylabel('Price of ETH (£)', fontsize=15)
        plt.xlabel('Date', fontsize=15)
        plt.title('ETH MA Crossover', fontsize=20)
        plt.legend()
        plt.show()


if __name__ == "__main__":
    foo = Candlesticks()
    foo.display_all_candle_data()
