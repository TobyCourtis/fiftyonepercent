from __future__ import annotations

from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.clients.helpers import epoch_to_date, convert_to_hours


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

    def plot_crossover(self, window_min, window_max, units="days"):
        """
        Main function used to plot the MA crossover

        :param window_min:  Short window size
        :param window_max:  Long window size
        :param units: units of window_min/max in days or hours
        :return: (void) Plots the MA crossover graph
        """
        main_df = self.create_ma_crossover_dataframe(window_min, window_max, units)

        # 'buy/sell' signals
        main_df['buy_sell_x'] = main_df['Position'].replace(0.0, np.NAN)
        main_df['buy_y'] = main_df.apply(lambda x: x['Short'] if x['buy_sell_x'] == 1.0 else np.NAN, axis=1)
        main_df['sell_y'] = main_df.apply(lambda x: x['Long'] if x['buy_sell_x'] == -1.0 else np.NAN, axis=1)

        # PLOTTING
        plt.figure(figsize=(20, 10))

        main_df['Close'].plot(color='k', label='Close Price')
        main_df['Short'].plot(color='b', label='Short Price')
        main_df['Long'].plot(color='g', label='Long Price')

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

    def get_current_position(self, dataframe):
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

    def shorten(self, limit=43_200):  # default to 30 days of candles in 1m intervals
        if type(limit) is not int:
            raise TypeError(f"Expected integer to shorten candles to but received '{type(limit)}'")
        if limit < 1:
            raise ValueError(f"Limit '{limit}' is not a valid positive integer to shorten the candle length to.")
        if len(self) <= limit:
            pass  # no need to shorten
        else:
            self.openTime = self.openTime[-limit:]
            self.open = self.open[-limit:]
            self.high = self.high[-limit:]
            self.low = self.low[-limit:]
            self.close = self.close[-limit:]
            self.volume = self.volume[-limit:]
            self.closeTime = self.closeTime[-limit:]
            self.quoteAssetVolume = self.quoteAssetVolume[-limit:]
            self.numberOfTrades = self.numberOfTrades[-limit:]
            self.takerBuyBaseAssetVolume = self.takerBuyBaseAssetVolume[-limit:]
            self.takerBuyQuoteAssetVolume = self.takerBuyQuoteAssetVolume[-limit:]
            self.ignore = self.ignore[-limit:]


if __name__ == "__main__":
    foo = Candlesticks()
    foo.display_all_candle_data()
