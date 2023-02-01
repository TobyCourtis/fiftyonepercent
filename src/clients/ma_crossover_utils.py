from src.clients.helpers import Side, OrderType
from src.notify import notifier, slack_image_upload

STOP_LOSS_MULTIPLIER = 0.80
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
    message = "Buy Signal - Order Executed."
    notify_current_transaction(message, latest_row, units, window_max, window_min)

    try:
        # 1. Buy all
        full_qty = client.get_market_position()
        client.market_order(Side.buy, full_qty)
        # 2. Remove stops
        client.cancel_all_open_orders_for_type(OrderType.stop_loss_limit)
        # 3. Replace stops
        stop_price = round(client.avg_price() * STOP_LOSS_MULTIPLIER, ETH_PRECISION)
        client.place_stop_order(stop_price)
    except Exception as e:
        print(f"Exception: {e}")
        notifier.slack_notify("Buy order just failed - please investigate!!", "prod-trades")


def sell(window_min, window_max, units, latest_row, client):
    message = "Sell Signal - Order Executed."
    notify_current_transaction(message, latest_row, units, window_max, window_min)

    try:
        # 1. Sell all
        full_qty = client.get_market_position()
        client.market_order(Side.sell, full_qty)
        # 2. Remove all stops
        client.cancel_all_open_orders_for_type(OrderType.stop_loss_limit)
    except Exception as e:
        print(f"Exception: {e}")
        notifier.slack_notify("Sell order just failed - please investigate!!", "prod-trades")


def send_update_snapshot(all_candles, client, window_min, window_max, units):
    all_candles.create_crossover_graph(window_min, window_max, units)
    slack_image_upload.upload_current_plot(window_min, window_max, units)
    client.position_summary()
    client.show_open_orders()
