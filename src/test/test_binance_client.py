import unittest
from unittest.mock import MagicMock, patch

from binance.spot import Spot

from src.clients.binance_client import BinanceClient
from src.clients.helpers import Side
from src.notify import notifier

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
            "price": "5",
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

mocked_spot_class = Spot()
mocked_spot_class.new_order = MagicMock(return_value=market_order_return_value)

notifier.slack_notify = MagicMock(return_value="nothing!")


class TestBinanceClient(unittest.TestCase):

    def test_market_order(self):
        tested_binance_client = BinanceClient(test=True)

        with patch.object(tested_binance_client, 'client', mocked_spot_class):
            self.assertEqual(tested_binance_client.client, mocked_spot_class)

            actual_order_message = tested_binance_client.market_order(Side.sell, 1, "ETHUSDT")
            expected_order_message = "Order filled - qty: 6.0 price: 54.17"

            self.assertEqual(actual_order_message, expected_order_message)
