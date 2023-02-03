import unittest
from unittest.mock import MagicMock

from src.clients import ma_crossover_utils
from src.clients.binance_client import BinanceClient
from src.clients.candlesticks import Candlesticks
from src.notify import notifier, slack_image_upload
from src.utils.utils import Side, OrderType

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
        fiat_total_amount = float(10.0)
        mocked_binance_client.account_balance_by_symbol = MagicMock(return_value=fiat_total_amount)
        mocked_binance_client.cancel_all_open_orders_for_type = MagicMock(return_value=None)
        mocked_binance_client.avg_price = MagicMock(return_value=float(1000.00))
        mocked_binance_client.place_stop_order = MagicMock(return_value=None)

        ma_crossover_utils.buy(1, 2, "hours", None, mocked_binance_client)

        mocked_binance_client.account_balance_by_symbol.assert_called_with("GBP")
        mocked_binance_client.market_order.assert_called_with(Side.buy, fiat_total_amount)
        mocked_binance_client.place_stop_order.assert_called_with(float(900.0))

    def test_ma_utils_sell_with_single_stop(self):
        mocked_binance_client = BinanceClient()
        order_id = 1234
        mocked_binance_client.get_open_order_ids = MagicMock(return_value=[order_id])
        crypto_total_amount = float(1.5)
        mocked_binance_client.account_balance_by_symbol = MagicMock(return_value=crypto_total_amount)
        mocked_binance_client.cancel_and_replace_with_sell = MagicMock(return_value=None)

        ma_crossover_utils.sell(1, 2, "hours", None, mocked_binance_client)

        mocked_binance_client.get_open_order_ids.assert_called_with(order_type_filter=OrderType.stop_loss_limit)
        mocked_binance_client.account_balance_by_symbol.assert_called_with("ETH", include_locked=True)
        mocked_binance_client.cancel_and_replace_with_sell.assert_called_with(order_id_to_cancel=order_id,
                                                                              qty_to_sell=crypto_total_amount)

    def test_ma_utils_sell_with_no_stops(self):
        mocked_binance_client = BinanceClient()
        mocked_binance_client.get_open_order_ids = MagicMock(return_value=[])
        crypto_total_amount = float(1.5)
        mocked_binance_client.cancel_all_open_orders_for_type = MagicMock(return_value=None)
        mocked_binance_client.account_balance_by_symbol = MagicMock(return_value=crypto_total_amount)
        mocked_binance_client.market_order = MagicMock(return_value=None)

        ma_crossover_utils.sell(1, 2, "hours", None, mocked_binance_client)

        mocked_binance_client.cancel_all_open_orders_for_type.assert_called_with(OrderType.stop_loss_limit)
        mocked_binance_client.get_open_order_ids.assert_called_with(order_type_filter=OrderType.stop_loss_limit)
        mocked_binance_client.account_balance_by_symbol.assert_called_with("ETH")
        mocked_binance_client.market_order.assert_called_with(Side.sell, crypto_total_amount)

    def test_ma_utils_sell_with_multiple_stops(self):
        mocked_binance_client = BinanceClient()
        mocked_binance_client.get_open_order_ids = MagicMock(return_value=[123, 456])
        crypto_total_amount = float(1.5)
        mocked_binance_client.cancel_all_open_orders_for_type = MagicMock(return_value=None)
        mocked_binance_client.account_balance_by_symbol = MagicMock(return_value=crypto_total_amount)
        mocked_binance_client.market_order = MagicMock(return_value=None)

        ma_crossover_utils.sell(1, 2, "hours", None, mocked_binance_client)

        mocked_binance_client.get_open_order_ids.assert_called_with(order_type_filter=OrderType.stop_loss_limit)
        mocked_binance_client.cancel_all_open_orders_for_type.assert_called_with(OrderType.stop_loss_limit)
        mocked_binance_client.account_balance_by_symbol.assert_called_with("ETH")
        mocked_binance_client.market_order.assert_called_with(Side.sell, crypto_total_amount)

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
