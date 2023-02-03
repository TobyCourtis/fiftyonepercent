import unittest

import pandas as pd

from src.types.candlesticks import Candlesticks
from src.utils.utils import Side


def variable_length_candlesticks(length):
    candles = Candlesticks()

    values = [i for i in range(1, length + 1)]

    candles.openTime += values
    candles.open += values
    candles.high += values
    candles.low += values
    candles.close += values
    candles.volume += values
    candles.closeTime += values
    candles.quoteAssetVolume += values
    candles.numberOfTrades += values
    candles.takerBuyBaseAssetVolume += values
    candles.takerBuyQuoteAssetVolume += values
    candles.ignore += values
    return candles


def some_candle():
    return variable_length_candlesticks(1)


class TestCandlesticks(unittest.TestCase):

    def test_shorten_candles_success(self):
        candles = variable_length_candlesticks(10)

        required_length = 3
        candles.shorten(required_length)

        self.assertEqual(len(candles), required_length)
        self.assertEqual(candles.open, [8, 9, 10])

    def test_shorten_candles_does_not_shorten_if_less_than_limit(self):
        starting_length = 3
        candles = variable_length_candlesticks(starting_length)

        required_length = 5
        candles.shorten(required_length)

        self.assertEqual(len(candles), starting_length)
        self.assertEqual(candles.open, [1, 2, 3])

    def test_shorten_fails_with_negative_value(self):
        starting_length = 5
        candles = variable_length_candlesticks(starting_length)

        required_length = -5

        self.assertRaises(ValueError, candles.shorten, required_length)

    def test_shorten_fails_if_non_int_passed(self):
        starting_length = 5
        candles = variable_length_candlesticks(starting_length)

        required_length = "blah"

        self.assertRaises(TypeError, candles.shorten, required_length)

    def test_position_1m_buy(self):
        df = pd.DataFrame([[0], [0], [0], [1]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 1)

    def test_position_1m_trailing_buy(self):
        df = pd.DataFrame([[0], [0], [1], [0]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 1)

    def test_position_1m_trailing_sell(self):
        df = pd.DataFrame([[0], [-1], [0], [0]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, -1)

    def test_position_15m_trailing_buy(self):
        df = pd.DataFrame([[0], [0], [1], [0]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '15m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 0)

    def test_position_15m_trailing_sell(self):
        df = pd.DataFrame([[0], [-1], [0], [0]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '15m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 0)

    def test_position_15m_buy(self):
        df = pd.DataFrame([[0], [0], [0], [1]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '15m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 1)

    def test_position_15m_sell(self):
        df = pd.DataFrame([[0], [0], [0], [-1]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '15m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, -1)

    def test_position_15m_unchanged(self):
        df = pd.DataFrame([[0], [0], [0], [0]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 0)

    def test_position_buy_sell_quick(self):
        df = pd.DataFrame([[1], [0], [-1], [0]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, -1)

    def test_position_1m_outrange(self):
        position_rows = [[0], [1], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]
        df = pd.DataFrame(position_rows, columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'

        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 0)

    def test_get_position(self):
        df = pd.DataFrame([[1]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'
        actual = candles.get_suggested_position(df)
        self.assertEqual(actual, 1)

    def test_add_candles(self):
        candles1 = Candlesticks()
        candles1.closeTime += [0]

        candles2 = some_candle()
        candles1.add(candles2)

        self.assertEqual(candles1.closeTime, [0, 1])

    def test_add_candles_with_invalid_start_date_throws_exception(self):
        candles1 = Candlesticks()
        candles1.closeTime += [5]  # later closing time

        candles2 = some_candle()

        self.assertRaises(Exception, candles1.add, candles2)

    def test_adding_candles_with_different_timeframes_fails(self):
        candles1 = Candlesticks()
        candles1.closeTime += [1]
        candles1.candleTimeframe = "FOO"

        candles2 = some_candle()
        candles2.candleTimeframe = "BAR"

        self.assertRaises(Exception, candles1.add, candles2)

    def test_suggested_position_type_buy(self):
        df = pd.DataFrame([[1]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'
        actual = candles.suggested_position_type(df)
        self.assertEqual(actual, Side.buy)

    def test_suggested_position_type_sell(self):
        df = pd.DataFrame([[-1]], columns=['Position'])

        candles = Candlesticks()
        candles.candleTimeframe = '1m'
        actual = candles.suggested_position_type(df)
        self.assertEqual(actual, Side.sell)
