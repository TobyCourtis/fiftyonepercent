import datetime
import time
import traceback

from src.notify import notifier, slack_image_upload
from src.utils.utils import Side, OrderType, add_spacing, bruce_buffer

STOP_LOSS_MULTIPLIER = 0.9
ETH_PRECISION = 8


def notify_current_transaction(message, latest_row, units, window_max, window_min):
    notifier.slack_notify(
        f"{message} "
        f"Time={latest_row.name}, "
        f"Short={latest_row['Short']}, "
        f"Long={latest_row['Long']}, "
        f"windowMin={window_min}, "
        f"windowMax={window_max}, "
        f"units={units}",
        "prod-trades")


def buy(window_min, window_max, units, latest_row, client):
    message = "MA Crossover buy process executed: "
    notify_current_transaction(message, latest_row, units, window_max, window_min)

    try:
        # 1. Buy all
        full_quantity_fiat: float = client.account_balance_by_symbol("GBP")
        client.market_order(Side.buy, full_quantity_fiat)

        # 2. Replace stops
        stop_price = round(client.avg_price() * STOP_LOSS_MULTIPLIER, ETH_PRECISION)
        client.place_stop_order(stop_price)
    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()
        notifier.slack_notify("MA Crossover buy process failed - please investigate!!", "prod-trades")


def sell(window_min, window_max, units, latest_row, client):
    message = "MA Crossover sell process executed: "
    notify_current_transaction(message, latest_row, units, window_max, window_min)

    try:
        # 1. Get STOP order IDs
        open_stop_order_ids = client.get_open_order_ids(order_type_filter=OrderType.stop_loss_limit)

        # Case 1 stop found
        if len(open_stop_order_ids) == 1:
            # 1. Get full crypto balance locked and free
            full_quantity_crypto = client.account_balance_by_symbol("ETH", include_locked=True)
            # 2. Cancel stop and replace with sell market order
            client.cancel_and_replace_with_sell(order_id_to_cancel=open_stop_order_ids[0],
                                                qty_to_sell=full_quantity_crypto)

        # Case many or no stops
        else:
            print("Cancelling stops then selling full balance")
            # 1. Remove all stops (many or none)
            client.cancel_all_open_orders_for_type(OrderType.stop_loss_limit)
            # 2. Sell all
            full_quantity_crypto = client.account_balance_by_symbol("ETH")
            client.market_order(Side.sell, full_quantity_crypto)

    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()
        notifier.slack_notify("MA Crossover sell process failed - please investigate!!", "prod-trades")


def send_update_snapshot(all_candles, client, window_min, window_max, units):
    all_candles.create_crossover_graph(window_min, window_max, units)
    slack_image_upload.upload_current_plot(window_min, window_max, units)
    client.position_summary()
    client.show_open_orders()


def sleep_until_next_candle_released(new_start_time):
    new_start_datetime = datetime.datetime.fromtimestamp(int(new_start_time / 1000))
    seconds_elapsed = (datetime.datetime.now() - new_start_datetime).total_seconds()
    sleep_time = 60 - seconds_elapsed
    if sleep_time <= 0:
        pass
    else:
        print(add_spacing(f"Waiting {sleep_time} seconds for new candles ..."))
        time.sleep(sleep_time)
    bruce_buffer()
