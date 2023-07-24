from __future__ import annotations

import os
from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.utils import epoch_to_date, convert_to_hours, Side


def plot_crossover_graph_from_dataframe(crossover_df, save_path=None):
    # 'buy/sell' signals
    crossover_df['buy_sell_x'] = crossover_df['Position'].replace(0.0, np.NAN)
    crossover_df['buy_y'] = np.where(crossover_df['buy_sell_x'] == 1.0, crossover_df['Short'], np.NAN)
    crossover_df['sell_y'] = np.where(crossover_df['buy_sell_x'] == -1.0, crossover_df['Long'], np.NAN)

    # downsample and remove unwanted data
    downsample_factor = 10  # 1 in downsample_factor rows are kept
    crossover_df.drop('Position', axis=1, inplace=True)
    crossover_df.drop('Signal', axis=1, inplace=True)

    downsampled_df = pd.DataFrame()
    downsampled_df['Close'] = crossover_df['Close'].copy()
    downsampled_df['Short'] = crossover_df['Short'].copy()
    downsampled_df['Long'] = crossover_df['Long'].copy()
    downsampled_df.reset_index(drop=True, inplace=True)
    crossover_df['Close'] = np.where(downsampled_df.index % downsample_factor == 0, downsampled_df['Close'], np.nan)
    crossover_df['Short'] = np.where(downsampled_df.index % downsample_factor == 0, downsampled_df['Short'], np.nan)
    crossover_df['Long'] = np.where(downsampled_df.index % downsample_factor == 0, downsampled_df['Long'], np.nan)

    crossover_df.dropna(how='all', inplace=True)  # drop all rows that are NAN for all columns

    # PLOTTING
    plt.figure(figsize=(20, 10))
    crossover_df['Close'].plot(color='k', label='Close Price')
    crossover_df['Short'].plot(color='b', label='Short Price')
    crossover_df['Long'].plot(color='g', label='Long Price')
    plt.plot(crossover_df['buy_sell_x'].index,
             crossover_df['buy_y'],
             '^', markersize=15, color='g', label='buy')
    # plot 'sell' signals
    plt.plot(crossover_df['buy_sell_x'].index,
             crossover_df['sell_y'],
             'v', markersize=15, color='r', label='sell')

    # METADATA
    plt.ylabel('Price of ETH (£)', fontsize=15)
    plt.xlabel('Date', fontsize=15)
    plt.title('ETH MA Crossover', fontsize=20)
    plt.legend()
    if save_path is None:
        plt.show()
    else:
        print(f"Saved crossover image to {save_path}")
        plt.savefig(save_path)
    plt.close()


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

        self.candleTimeframe = "NONE"

    def __len__(self):
        return len(self.openTime)  # essentially equals No. candles

    def display_all_candle_data(self):
        pprint(vars(self))

    def number_candles_in_one_hour(self):
        match self.candleTimeframe[-1]:
            case "m":
                amount = int(self.candleTimeframe[:-1])
                return int(60 / amount)  # 15m=4, 1m=60
            case "h":
                return 1
            case _:
                raise Exception(f"Timeframe '{self.candleTimeframe}' is not supported yet!")

    def create_crossover_graph(self, window_min, window_max, units="days", save=True):
        """
        Main function used to plot the MA crossover

        :param window_min:  Short window size
        :param window_max:  Long window size
        :param save: Toggles save or display of graph snapshot to plot
        :param units: units of window_min/max in days or hours
        :return: (void) Plots the MA crossover graph
        """
        main_df = self.create_ma_crossover_dataframe(window_min, window_max, units)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = f"{current_dir}/../live/current_plot_snapshot.png"
        plot_crossover_graph_from_dataframe(main_df, file_path)

    def create_ma_crossover_dataframe(self, window_min, window_max, units):
        """
        Creates dataframe housing MA Crossover information

        :param window_min:  Short window size
        :param window_max:  Long window size
        :param units: units of window_min/max in days or hours
        :return: MA Crossover dataframe
        """
        main_df = pd.DataFrame(self.close, columns=['Close'])
        df_close_time = pd.DataFrame(self.closeTime, columns=['CloseTime'])
        number_candles_in_one_hour = self.number_candles_in_one_hour()

        # convert window size into the smallest factor (hours)
        window_min, window_max = convert_to_hours(window_min, window_max, units)

        # adjust window size from hours to match intervals of 1m, 15m or 1h
        window_min = window_min * number_candles_in_one_hour
        window_max = window_max * number_candles_in_one_hour

        main_df.index = df_close_time['CloseTime'].apply(epoch_to_date)
        main_df['Short'] = main_df['Close'].rolling(window=window_min).mean()
        main_df['Long'] = main_df['Close'].rolling(window=window_max).mean()
        main_df.dropna(inplace=True)  # important to happen here or signal/position skewed
        main_df['Signal'] = np.where(main_df['Short'] > main_df['Long'], 1.0, 0.0)
        main_df['Position'] = main_df['Signal'].diff()
        main_df = main_df.astype(float)
        return main_df

    def get_suggested_position(self, dataframe):
        # return the latest non 0 within values within a time frame
        match self.candleTimeframe:
            case "1m":
                look_back_window = 10  # 10 minute look back window for signals, Check the last signal.
            case "15m":
                look_back_window = 1
            case "1h":
                look_back_window = 1
            case _:
                raise Exception(f"Timeframe '{self.candleTimeframe}' is not supported!")

        dataframe = dataframe.iloc[-look_back_window:]
        dataframe = dataframe[dataframe['Position'] != 0]
        if len(dataframe) == 0:
            position = 0
        else:
            position = dataframe.iloc[-1, -1]
        return position

    def suggested_position_type(self, dataframe) -> Side | None:
        match self.get_suggested_position(dataframe):
            case 1:
                return Side.buy
            case -1:
                return Side.sell
            case 0:
                return None

            case _:
                raise Exception(f"Invalid suggested position was returned, expected buy/sell/hold.")

    def add(self, candles: Candlesticks):
        if self.closeTime[-1] > candles.openTime[0]:
            raise Exception(f"Candlesticks being appended have open time before closing time of current candlesticks")
        if self.candleTimeframe != candles.candleTimeframe:
            raise Exception(
                f"Cannot add candles with different timeframes ({self.candleTimeframe} and {candles.candleTimeframe}")

        self.openTime += candles.openTime
        self.open += candles.open
        self.high += candles.high
        self.low += candles.low
        self.close += candles.close
        self.volume += candles.volume
        self.closeTime += candles.closeTime
        self.quoteAssetVolume += candles.quoteAssetVolume
        self.numberOfTrades += candles.numberOfTrades
        self.takerBuyBaseAssetVolume += candles.takerBuyBaseAssetVolume
        self.takerBuyQuoteAssetVolume += candles.takerBuyQuoteAssetVolume
        self.ignore += candles.ignore

    def shorten(self, from_limit=43_200, to_limit=None):  # default to 30 days of candles in 1m intervals
        if type(from_limit) is not int:
            raise TypeError(f"Expected integer to shorten candles to but received '{type(from_limit)}'")
        if from_limit < 1:
            raise ValueError(f"Limit '{from_limit}' is not a valid positive integer to shorten the candle length to.")
        if len(self) < from_limit:
            pass  # no need to shorten
        if to_limit is not None:
            if to_limit > from_limit:
                raise ValueError(f"To limit ({to_limit}) cannot be larger than from limit ({from_limit})")

        # TODO - refactor into looping through a list of candlesticks attrs and calling a lamda to shorten to limit
        self.openTime = self.openTime[-from_limit:]
        self.open = self.open[-from_limit:]
        self.high = self.high[-from_limit:]
        self.low = self.low[-from_limit:]
        self.close = self.close[-from_limit:]
        self.volume = self.volume[-from_limit:]
        self.closeTime = self.closeTime[-from_limit:]
        self.quoteAssetVolume = self.quoteAssetVolume[-from_limit:]
        self.numberOfTrades = self.numberOfTrades[-from_limit:]
        self.takerBuyBaseAssetVolume = self.takerBuyBaseAssetVolume[-from_limit:]
        self.takerBuyQuoteAssetVolume = self.takerBuyQuoteAssetVolume[-from_limit:]
        self.ignore = self.ignore[-from_limit:]

        if to_limit is not None:
            self.openTime = self.openTime[:-to_limit]
            self.open = self.open[:-to_limit]
            self.high = self.high[:-to_limit]
            self.low = self.low[:-to_limit]
            self.close = self.close[:-to_limit]
            self.volume = self.volume[:-to_limit]
            self.closeTime = self.closeTime[:-to_limit]
            self.quoteAssetVolume = self.quoteAssetVolume[:-to_limit]
            self.numberOfTrades = self.numberOfTrades[:-to_limit]
            self.takerBuyBaseAssetVolume = self.takerBuyBaseAssetVolume[:-to_limit]
            self.takerBuyQuoteAssetVolume = self.takerBuyQuoteAssetVolume[:-to_limit]
            self.ignore = self.ignore[:-to_limit]


if __name__ == "__main__":
    foo = Candlesticks()
    foo.display_all_candle_data()
