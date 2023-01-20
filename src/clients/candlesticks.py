from pprint import pprint

import matplotlib.pyplot as plt
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

    def display_all_candle_data(self):
        pprint(vars(self))

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

        match units.lower():
            case "days":
                conversion_factor = 24
            case "hours":
                conversion_factor = 1
            case _:
                raise Exception(f"Unit '{units}' is not supported yet!")

        window_min = window_min * conversion_factor
        window_max = window_max * conversion_factor

        main_df['Short'] = main_df['Close'].rolling(window=window_min).mean()
        main_df['Long'] = main_df['Close'].rolling(window=window_max).mean()

        main_df.index = df_close_time['CloseTime'].apply(epoch_to_date)

        main_df.dropna(inplace=True)
        main_df = main_df.astype(float)

        main_df.plot()
        plt.show()


if __name__ == "__main__":
    foo = Candlesticks()
    foo.display_all_candle_data()
