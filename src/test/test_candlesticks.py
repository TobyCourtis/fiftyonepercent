import unittest

from . import Candlesticks
import pandas as pd


class TestCandlesticks(unittest.TestCase):
    def test_get_signal(self):
        df = pd.DataFrame([[123]], columns=['Signal'])

        actual = Candlesticks.get_current_signal(None, df)
        self.assertEqual(actual, 123)
