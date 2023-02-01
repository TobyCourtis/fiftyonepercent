import unittest
from unittest.mock import MagicMock

from src.clients import ma_crossover_utils
from src.clients.binance_client import BinanceClient
from src.clients.candlesticks import Candlesticks
from src.clients.helpers import Side, OrderType
from src.notify import notifier, slack_image_upload

"""
GLOBAL MOCKS
"""
notifier.slack_notify = MagicMock(return_value="Not calling slack!")

ma_crossover_utils.notify_current_transaction = MagicMock(return_value="Not notifying!")
""""""


class TestMACrossoverUtils(unittest.TestCase):

    def test_ma_utils_buy(self):
        mocked_binance_client = BinanceClient()
        mocked_binance_client.market_order = MagicMock(return_value=None)
        mocked_binance_client.cancel_all_open_orders_for_type = MagicMock(return_value=None)
        fiat_total_amount = float(10.0)
        mocked_binance_client.coin_info = MagicMock(return_value=fiat_total_amount)
        mocked_binance_client.cancel_all_open_orders_for_type = MagicMock(return_value=None)
        mocked_binance_client.avg_price = MagicMock(return_value=float(1000.00))
        mocked_binance_client.place_stop_order = MagicMock(return_value=None)

        ma_crossover_utils.buy(1, 2, "hours", None, mocked_binance_client)

        mocked_binance_client.coin_info.assert_called_with("GBP")
        mocked_binance_client.market_order.assert_called_with(Side.buy, fiat_total_amount)
        mocked_binance_client.cancel_all_open_orders_for_type.assert_called_with(OrderType.stop_loss_limit)
        mocked_binance_client.place_stop_order.assert_called_with(float(900.0))

    def test_ma_utils_sell(self):
        mocked_binance_client = BinanceClient()
        mocked_binance_client.market_order = MagicMock(return_value=None)
        mocked_binance_client.cancel_all_open_orders_for_type = MagicMock(return_value=None)
        crypto_total_amount = float(1.5)
        mocked_binance_client.get_market_position = MagicMock(return_value=crypto_total_amount)

        ma_crossover_utils.sell(1, 2, "hours", None, mocked_binance_client)

        self.assertTrue(mocked_binance_client.get_market_position.called)
        mocked_binance_client.market_order.assert_called_with(Side.sell, crypto_total_amount)
        mocked_binance_client.cancel_all_open_orders_for_type.assert_called_with(OrderType.stop_loss_limit)

    def test_send_update_snapshot(self):
        mocked_binance_client = BinanceClient()
        mock_candles = Candlesticks()
        mock_candles.create_crossover_graph = MagicMock(return_value=None)
        slack_image_upload.upload_current_plot = MagicMock(return_value=None)
        mocked_binance_client.position_summary = MagicMock(return_value=None)
        mocked_binance_client.show_open_orders = MagicMock(return_value=None)

        ma_crossover_utils.send_update_snapshot(mock_candles, mocked_binance_client, 1, 2, 'hours')

        mock_candles.create_crossover_graph.assert_called_with(1, 2, "hours")
        slack_image_upload.upload_current_plot.assert_called_with(1, 2, "hours")
        self.assertTrue(mocked_binance_client.position_summary.called)
        self.assertTrue(mocked_binance_client.show_open_orders.called)
