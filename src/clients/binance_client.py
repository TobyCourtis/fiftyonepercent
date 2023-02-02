import datetime
import datetime as dt
import json
import os
from pprint import pprint

import numpy as np
import pandas as pd
from binance.error import ClientError
from binance.spot import Spot
from pandas import DataFrame

from src.clients.candlesticks import Candlesticks
from src.clients.helpers import Side, epoch_to_date, create_image_from_dataframe, OrderType, add_spacing, PositionType, \
    round_down_to_decimal_place
from src.notify import notifier, slack_image_upload


class BinanceClient:
    PRECISION = 8  # from exchange_info ETH PRECISION is 8 for test and prod
    TICK_SIZE = 0.01  # from exchange_info symbol filterType PRICE_FILTER
    MIN_PRICE = 0.01

    def __init__(self, **kwargs):
        if "test" in kwargs:
            test = kwargs["test"]
        else:
            test = True

        self.test = test  # allow usage globally

        if test:
            key_path = os.path.dirname(__file__) + "/../keys/testnet-keys.json"
            base_url = "https://testnet.binance.vision"
        else:
            key_path = os.path.dirname(__file__) + "/../keys/default-keys.json"
            base_url = "https://api.binance.com"

        with open(key_path) as json_data:
            keys = json.loads(json_data.read())
            API_KEY = keys["API_KEY"]
            API_SECRET = keys["API_SECRET"]

        self.client = Spot(key=API_KEY, secret=API_SECRET, base_url=base_url)
        print(f"Initialised BinanceClient with test mode: {test}")

    """
    MISC
    """

    def exchange_info(self):
        """
        Current exchange trading rules and symbol information
        :return: Large dictionary of exchange information
        """
        exchange_info = self.client.exchange_info()
        return exchange_info

    """
    ACCOUNT INFORMATION
    """

    def all_account_info(self):
        print("Account Info")
        acc_info = self.client.account(recvWindow=60000)  # TODO time sync and lower recvWindow
        for i in acc_info:
            if i == 'balances':
                print("balance:")
                for currency in acc_info[i]:
                    pprint(currency)
            else:
                print(f"{i}: {acc_info[i]}")

    def account_balance_by_symbol(self, symbol="ETH") -> float:
        """

        :param symbol: Symbol (Note in account balance, the raw crypto symbol is used e.g. ETH not ETHGBP)
        :return: float for account balance of input symbol
        """
        account_info = self.client.account(recvWindow=60000)
        for key, value in account_info.items():
            if key == 'balances':
                for balance in value:
                    if balance['asset'] == symbol:
                        available_balance = float(balance['free'])
                        print(f"Balance ({symbol}): {available_balance}")
                        return available_balance
        print(f"No balance found for {symbol}")
        return 0.0

    """
    POSITION/PNL INFORMATION
    """

    def show_open_orders(self, order_type_filter=None, save_image=True) -> DataFrame:

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        try:
            response = self.client.get_open_orders(symbol, recvWindow=60000)
            if len(response) == 0:
                if not self.test:
                    notifier.slack_notify("No live orders",
                                          "prod-trades")
                print(f"No live orders were found. Environment Test={self.test}, OrderTypeFilter={order_type_filter}")
                return pd.DataFrame([])
            open_orders = []
            for order_info in response:
                order = {
                    'OrderId': order_info['orderId'],
                    'Symbol': order_info['symbol'],
                    'Side': order_info['side'],
                    'Price': float(order_info['price']),
                    'OrigQty': float(order_info['origQty']),
                    'ExecutedQty': float(order_info['executedQty']),
                    'Status': order_info['status'],
                    'timeInForce': order_info['timeInForce'],
                    'Type': order_info['type'],
                    'Time': epoch_to_date(order_info['time'])
                }
                open_orders.append(order)
            open_orders = pd.DataFrame(open_orders)

            if order_type_filter is not None:
                param_type = type(order_type_filter)
                if param_type != OrderType:
                    raise TypeError(f"Parameter order_type_filter should be of type OrderType not {param_type}")
                else:
                    # drop rows if type does not match input param
                    open_orders = open_orders.drop(open_orders[open_orders.Type != order_type_filter.value].index)

                    if len(open_orders) == 0:
                        if not self.test:
                            notifier.slack_notify("No live orders",
                                                  "prod-trades")
                        print(f"No live orders were found for order type {order_type_filter.value} "
                              f"Environment Test={self.test}")
                        return open_orders
                    else:
                        print(add_spacing(f"Showing all orders of type '{order_type_filter.value}':"))

            open_orders.set_index('Symbol', inplace=True)

            current_dir = os.path.dirname(os.path.realpath(__file__))
            open_orders_path = f"{current_dir}/../clients/current_open_orders_snapshot.png"

            print(open_orders)
            if save_image:
                create_image_from_dataframe(open_orders, open_orders_path, "Open Orders")
            if not self.test:
                slack_image_upload.upload_image(open_orders_path, "PnL", f"Number of Open Orders - {len(response)}")
            return open_orders

        except ClientError as error:
            print(
                "Unable to Pull Order - Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    def get_market_position(self, symbol=None):
        """

        Function to return the current net position of the coin that is passed

        :return: float of position
        """
        if symbol is None:
            symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        qty = 0
        try:
            trade_history = self.client.my_trades(symbol=symbol, recvWindow=60000)
            if len(trade_history) == 0:
                print(add_spacing(f"Current qty: {0}"))
                return 0

            for trade_info in trade_history:
                trade_qty = float(trade_info['qty']) if trade_info['isBuyer'] == True else float(trade_info['qty']) * -1
                qty += round(trade_qty, self.PRECISION)
            rounded_qty = round(qty, self.PRECISION)
            print(add_spacing(f"Current qty: {rounded_qty}"))
            return rounded_qty

        except ClientError as error:
            print(
                "Unable to pull trades - Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    def get_market_position_type(self, symbol=None) -> PositionType:
        """
        Return PositionType meaning are we currently in a state of BOUGHT or SOLD our holdings

        :param symbol: Symbol
        :return: PositionType (bought OR sold)
        """
        threshold = 0.00076  # £1 buys this much ETH
        return PositionType.sold if self.get_market_position(symbol) < threshold else PositionType.bought

    def position_summary(self, symbol_list=None) -> pd.DataFrame:
        """

        Function to return the position and PnL of each coin holding

        :param symbol_list: list of coins that you want included in the report
        :return: Dataframe showing the coins in the index and pnl in the columns. DF will include WAP.
        """

        if symbol_list is None:
            symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now
            symbol_list = [symbol]

        if len(symbol_list) == 0:
            raise Exception("No input symbols found. Please provide no parameter or at least one symbol.")

        total_df = None
        try:
            pnl_df = []
            for symbol in symbol_list:
                trade_history = self.client.my_trades(symbol=symbol)
                live_px = float(self.client.ticker_price(symbol=symbol)['price'])
                symbol_data = []
                for trade_info in trade_history:
                    coin_data = {}
                    coin_data['Symbol'] = trade_info['symbol']
                    coin_data['QTY'] = float(trade_info['qty']) if trade_info['isBuyer'] == True else float(
                        trade_info['qty']) * -1
                    coin_data['WAP'] = float(trade_info['price']) * float(trade_info['qty'])
                    coin_data['FEE'] = float(trade_info['commission'])
                    coin_data['Side'] = 'Buy' if trade_info['isBuyer'] == True else 'Sell'  # 1 is buy and 0 Sell
                    coin_data['PnL'] = ((live_px - float(trade_info['price'])) * float(coin_data['QTY'])) - float(
                        trade_info['commission'])
                    symbol_data.append(coin_data)
                symbol_data = pd.DataFrame(symbol_data)
                symbol_data = symbol_data.groupby(['Symbol', 'Side']).sum()
                symbol_data['WAP'] = abs(symbol_data['WAP'] / symbol_data['QTY'])
                symbol_data.reset_index(inplace=True)
                total_df = pd.DataFrame(
                    [symbol, 'Total', symbol_data.QTY.sum(), np.nan, symbol_data.FEE.sum(), symbol_data.PnL.sum()],
                    index=symbol_data.columns).T
                symbol_data = symbol_data.append(total_df)
                pnl_df.append(symbol_data)

            pnl_df = pd.concat(pnl_df, axis=1)
            pnl_df.set_index('Symbol', inplace=True)
            pnl_df[['QTY', 'WAP', 'FEE', 'PnL']] = (pnl_df[['QTY', 'WAP', 'FEE', 'PnL']].astype(float)).round(1)
            pnl_df = pnl_df.replace(np.nan, "-")

            current_dir = os.path.dirname(os.path.realpath(__file__))
            pnl_snapshot_path = f"{current_dir}/../clients/current_pnl_snapshot.png"
            create_image_from_dataframe(pnl_df, pnl_snapshot_path, "PnL Summary")

            print(pnl_df)
            if not self.test:
                slack_image_upload.upload_image(pnl_snapshot_path, "PnL",
                                                f"PnL Tables - PnL: {round(total_df.loc[0, 'PnL'], 2)} Qty: {round(total_df.loc[0, 'QTY'], 2)}")
            return pnl_df


        except ClientError as error:
            print(
                "Unable to pull report summary - Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    """
    MARKET INFORMATION
    """

    def coin_info(self, symbol=None) -> float:
        if self.test:
            raise Exception("This function is not supported in test environment")

        if symbol is None:
            symbol = "ETHGBP"  # only ETH supported for now

        coin_info = self.client.coin_info()
        for coin in coin_info:
            if coin["coin"] == symbol:
                print(add_spacing(f"{symbol} balance: {coin['free']}"))
                return float(coin['free'])
        return 0.0

    def avg_price(self, symbol=None) -> float:
        if symbol is None:
            symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now
        avg_price_response = self.client.avg_price(symbol)
        avg_price = float(avg_price_response["price"])
        print(f"Average price now: {avg_price}")
        return avg_price  # does not need rounding as it's straight from Binance

    def ticker_price(self, symbol="ETHUSDT"):
        print(self.client.ticker_price(symbol=symbol))

    def get_klines(self, timeframe="1m", **kwargs) -> Candlesticks:
        """
        This is the main marketplace data return function

        :param timeframe: the interval of candlestick, e.g 1s, 1m, 5m, 1h, 1d, etc.
        :param kwargs: period of time to begin candles from time now minus,  e.g days=1, hours=0, weeks=0, minutes=0
        :return: Candlesticks object. Containing list of candles.
        """
        timeNow = datetime.datetime.now().timestamp() * 1000
        if "startTime" in kwargs:
            startTime = kwargs['startTime']
        else:
            startTime = (datetime.datetime.now() - datetime.timedelta(**kwargs)).timestamp() * 1000

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        gathered_all_klines = False
        all_candles = Candlesticks()
        all_candles.candleTimeframe = timeframe

        call_count = 1
        while not gathered_all_klines:
            print(f"Candle API call count: {call_count}")
            call_count += 1

            klines = self.client.klines(interval=timeframe,
                                        limit=1000,
                                        symbol=symbol,
                                        startTime=int(startTime),
                                        endTime=int(timeNow))

            for kline in klines:
                all_candles.openTime.append(kline[0])
                all_candles.open.append(kline[1])
                all_candles.high.append(kline[2])
                all_candles.low.append(kline[3])
                all_candles.close.append(kline[4])
                all_candles.volume.append(kline[5])
                all_candles.closeTime.append(kline[6])
                all_candles.quoteAssetVolume.append(kline[7])
                all_candles.numberOfTrades.append(kline[8])
                all_candles.takerBuyBaseAssetVolume.append(kline[9])
                all_candles.takerBuyQuoteAssetVolume.append(kline[10])
                all_candles.ignore.append(kline[11])

            # check if API response limit met
            if len(klines) < 1000:
                gathered_all_klines = True
            else:
                startTime = all_candles.closeTime[-1]  # renew data pull from latest candle close time
        return all_candles

    def ticker_24h(self):
        """
        24hr Ticker Price Change Statistics for symbol (for now only ETH)
        :return: 24hour rolling window price change statistics.
        """
        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now
        return self.client.ticker_24hr(symbol)

    """
    TRADE FUNCTIONS
    """

    def market_order(self, side: Side, qty: float, symbol=None):
        if symbol is None:
            symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        if not isinstance(side, Side):
            raise TypeError('Side must be Equal to BUY or SELL')

        params = {
            "symbol": symbol,
            "side": side.value,
            "type": OrderType.market.value,
            "quantity": str(qty),
            "timestamp": int(round(dt.datetime.now().timestamp()))
        }

        print(f"Order to {side.value} {symbol}:")

        try:
            response = self.client.new_order(**params)
            fills = response['fills']
            qty = 0
            wap = 0
            for fill in fills:
                wap += float(fill['qty']) * float(fill['price'])
                qty += float(fill['qty'])
            wap = wap / qty
            order_message = "Order filled - qty: %s price: %s" % (round(qty, 2), round(wap, 2))
            if not self.test:
                notifier.slack_notify(order_message, "prod-trades")
            return order_message
        except ClientError as error:
            print(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )

    def place_limit_order(self, side, price):
        """
        TEST ONLY
        """

        if not self.test:
            raise Exception("This function is currently not enabled for production - no use case for stops")

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        quantity = str(1)  # TODO when using limits make this

        params = {
            "symbol": symbol,
            "side": side.value,
            "type": OrderType.limit.value,
            "quantity": quantity,  # we will have to dynamically buy quantity based on price we have. Rounding important
            "timestamp": int(round(dt.datetime.now().timestamp())),
            "price": price,
            "timeInForce": "GTC"
        }

        print(f"Placing order for {symbol}: quantity={quantity}, price={price}")
        response = self.client.new_order(**params)
        print("\nResponse:")
        pprint(response)

    def place_stop_order(self, stop_price):
        """
        Places stop order for ALL current position

        :param stop_price: Stop price in fiat currency
        :return: Response from Binance API
        """

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        quantity = str(self.get_market_position())  # get quantity of ALL of our current holdings
        price = stop_price * 0.95
        params = {
            "symbol": symbol,
            "side": Side.sell.value,  # for now always a sell order
            "type": OrderType.stop_loss_limit.value,
            "quantity": quantity,
            "timestamp": int(round(dt.datetime.now().timestamp())),
            "timeInForce": "GTC",  # place stop until we remove
            "stopPrice": stop_price,
            "price": price,  # price for limit order 5% less than the stop_price
        }

        print(f"Placing stop order for {symbol}: quantity={quantity}, stop_price={stop_price}, price={price}")
        response = self.client.new_order(**params)
        print("\nResponse:")
        pprint(response)
        return response

    def remove_and_replace_stop(self, new_price):
        """
        UNIMPLEMENTED
        """
        # TODO - Implement if faster than cancel + place method
        return f"Remove current stop and place another"

    def cancel_all_open_orders_for_type(self, order_type: OrderType = None):
        """
        Cancels all orders of specific order type

        :param order_type: OrderType for which all orders will be cancelled
        :return: Message
        """
        if order_type is None:
            return self.cancel_all_open_orders()

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        open_orders_df = self.show_open_orders(order_type_filter=order_type, save_image=False)

        if len(open_orders_df) == 0:
            output = f"No orders of type {order_type.value} were found. Exiting."
            print(output)
            return output

        order_ids = open_orders_df['OrderId'].tolist()
        for order_id in order_ids:
            res = self.client.cancel_order(symbol=symbol, orderId=order_id)
            if res['status'] != "CANCELED":
                raise Exception("Order was not cancelled - FIX ME")
            msg = f"Cancelled order ID {order_id} for {symbol}. " \
                  f"Price={res['price']}, " \
                  f"origQty={res['origQty']} " \
                  f"type={res['type']} " \
                  f"side={res['side']}"
            if not self.test:
                notifier.slack_notify(msg, "prod-trades")
            print(msg)

        return f"Cancelled all orders of type {order_type}"

    def cancel_all_open_orders(self):
        """
        Cancells all orders regardless of type currently for Ethereum only

        :return: Response from Binance API
        """

        symbol = "ETHUSDT" if self.test else "ETHGBP"  # only ETH supported for now

        # TODO try catch for if no orders are currently placed

        open_orders = self.show_open_orders(save_image=False)

        if len(open_orders) == 0:
            return f"You have no open orders, exiting."

        response = self.client.cancel_open_orders(symbol)  # requires order to be open
        print(add_spacing("Response:"))
        print(response)
        return response


if __name__ == "__main__":
    client = BinanceClient(test=True)
    client.market_order(Side.sell, 1)
    print(client.position_summary())

    print("Finished and exited")
