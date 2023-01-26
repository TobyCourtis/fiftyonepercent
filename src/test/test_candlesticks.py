import unittest

import pandas as pd

from . import Candlesticks


class TestCandlesticks(unittest.TestCase):
    def test_diff_up(self):
        df = pd.DataFrame([[0], [1]], columns=['Signal'])

        df['Position'] = df['Signal'].diff()
        df.dropna(inplace=True)
        actual = Candlesticks.get_current_position(None, df)
        self.assertEqual(actual, 1)

    def test_diff_down(self):
        df = pd.DataFrame([[1], [0]], columns=['Signal'])

        df['Position'] = df['Signal'].diff()
        df.dropna(inplace=True)
        actual = Candlesticks.get_current_position(None, df)
        self.assertEqual(actual, -1)

    def test_diff_unchaged(self):
        df = pd.DataFrame([[1], [1]], columns=['Signal'])

        df['Position'] = df['Signal'].diff()
        df.dropna(inplace=True)
        actual = Candlesticks.get_current_position(None, df)
        self.assertEqual(actual, 0)

    def test_get_position(self):
        df = pd.DataFrame([[123]], columns=['Position'])

        actual = Candlesticks.get_current_position(None, df)
        self.assertEqual(actual, 123)

    def test_add_candles(self):
        candles1 = Candlesticks()
        candles1.closeTime += [1]

        candles2 = self.some_candle()
        candles1.add(candles2)

        self.assertEqual(candles1.closeTime, [1, 2])

    def some_candle(self):
        candles2 = Candlesticks()
        candles2.openTime += [1]
        candles2.closeTime += [2]
        return candles2

    def test_add_candles_with_invalid_start_date_throws_exception(self):
        candles1 = Candlesticks()
        candles1.closeTime += [5]  # later closing time

        candles2 = self.some_candle()

        self.assertRaises(Exception, candles1.add, candles2)

    def test_adding_candles_with_different_timeframes_fails(self):
        candles1 = Candlesticks()
        candles1.closeTime += [1]
        candles1.candleTimeframe = "FOO"

        candles2 = self.some_candle()
        candles2.candleTimeframe = "BAR"

        self.assertRaises(Exception, candles1.add, candles2)
