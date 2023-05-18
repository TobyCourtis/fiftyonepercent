import unittest
from unittest.mock import MagicMock, patch

from binance.spot import Spot

from src.client.binance_client import BinanceClient
from src.notify import notifier
from src.utils.utils import Side, PositionType

market_order_return_value = {
    "symbol": "BTCUSDT",
    "orderId": 28,
    "orderListId": -1,
    "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
    "transactTime": 1507725176595,
    "price": "0.00000000",
    "origQty": "10.00000000",
    "executedQty": "10.00000000",
    "cummulativeQuoteQty": "10.00000000",
    "status": "FILLED",
    "timeInForce": "GTC",
    "type": "MARKET",
    "side": "SELL",
    "strategyId": 1,
    "strategyType": 1000000,
    "workingTime": 1507725176595,
    "selfTradePreventionMode": "NONE",
    "fills": [
        {
            "price": "6",
            "qty": "1.00000000",
            "commission": "4.00000000",
            "commissionAsset": "USDT",
            "tradeId": 56
        },
        {
            "price": "10",
            "qty": "2.0",
            "commission": "19.99500000",
            "commissionAsset": "USDT",
            "tradeId": 57
        },
        {
            "price": "100",
            "qty": "3.0",
            "commission": "7.99600000",
            "commissionAsset": "USDT",
            "tradeId": 58
        }
    ]
}

kline = [
    1499040000000,
    "0.01634790",
    "0.80000000",
    "0.01575800",
    "0.01577100",
    "148976.11427815",
    1499644799999,
    "2434.19055334",
    308,
    "1756.87402397",
    "28.46694368",
    "17928899.62484339"
]

mocked_spot_class = Spot()
mocked_spot_class.new_order = MagicMock(return_value=market_order_return_value)
mocked_spot_class.klines = MagicMock(side_effect=[ConnectionError("TEST - Somethiing went wrong"),
                                                  [kline for x in range(30)]])

failing_spot_class = Spot()
failing_spot_class.klines = MagicMock(side_effect=ConnectionError("TEST - Somethiing went wrong"))

notifier.slack_notify = MagicMock(return_value="nothing!")

BELOW_THRESHOLD = 0.00075
ABOVE_THRESHOLD = 0.00076


def mock_market_position_holding(first):
    return ABOVE_THRESHOLD


def mock_market_position_sold(first):
    return BELOW_THRESHOLD


def account_balance_by_symbol_bought(one, two):
    return ABOVE_THRESHOLD


def account_balance_by_symbol_sold(one, two):
    return BELOW_THRESHOLD


class TestBinanceClient(unittest.TestCase):

    def test_get_klines_fail_then_pass(self):
        # given binance client
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'client', mocked_spot_class):
            self.assertEqual(tested_binance_client.client, mocked_spot_class)

            # when get klines
            all_candles = tested_binance_client.get_klines(timeframe="1m", hours=17)

            # then klines expected even after a connection errors
            self.assertEqual(len(all_candles), 30)

    def test_get_klines_only_fail(self):
        # given binance client that causes constant connection errors
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'client', failing_spot_class):
            self.assertEqual(tested_binance_client.client, failing_spot_class)

            # when get klines
            # then assert Exception was raised
            with self.assertRaises(Exception):
                tested_binance_client.get_klines(timeframe="1m", hours=17)

    def test_market_order(self):
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'client', mocked_spot_class):
            self.assertEqual(tested_binance_client.client, mocked_spot_class)

            actual_order_message = tested_binance_client.market_order(Side.sell, 1, "ETHUSDT")
            expected_order_message = "SELL order filled. Qty: 6.0 price: 54.33333333"

            self.assertEqual(actual_order_message, expected_order_message)

    def test_get_market_position_type_bought(self):
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'get_market_position', new=mock_market_position_holding):
            actual_position_type = tested_binance_client.get_market_position_type()
            expected_position_type = PositionType.bought

            self.assertEqual(actual_position_type, expected_position_type)

    def test_get_market_position_type_sold(self):
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'get_market_position', new=mock_market_position_sold):
            actual_position_type = tested_binance_client.get_market_position_type()
            expected_position_type = PositionType.sold

            self.assertEqual(actual_position_type, expected_position_type)

    def test_get_account_balance_position_type_bought(self):
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'account_balance_by_symbol', new=account_balance_by_symbol_bought):
            actual_balance_position_type = tested_binance_client.get_account_balance_position_type()
            expected_balance_position_type = PositionType.bought

            self.assertEqual(actual_balance_position_type, expected_balance_position_type)

    def test_get_account_balance_position_type_sold(self):
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'account_balance_by_symbol', new=account_balance_by_symbol_sold):
            actual_balance_position_type = tested_binance_client.get_account_balance_position_type()
            expected_balance_position_type = PositionType.sold

            self.assertEqual(actual_balance_position_type, expected_balance_position_type)
