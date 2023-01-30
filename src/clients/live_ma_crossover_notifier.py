import time

from binance_client import BinanceClient
from helpers import epoch_to_date, epoch_to_minutes, bruce_buffer, add_spacing, PositionType, Side
from src.notify import notifier, slack_image_upload


def notify_ma_crossover(window_min, window_max, units):
    """

    Main function to notify in the case of a MA crossover.
    - Gets as many candles as required for window_max
    - Keeps fetching each minute for new 1m interval candles
    - Generates dataframe for current candles
    - Notifies if position is buy or sell (also prints tail of current dataframe)

    :param window_min:  Short window size
    :param window_max:  Long window size
    :param units: units of window_min/max in days or hours
    :return: (void) Notifies if we should buy or sell
    """
    client = BinanceClient(test=False)

    # initialise 30 days of candles
    all_candles = client.get_klines(days=30)

    while True:
        new_start_time = all_candles.closeTime[-1]  # start from last candle closing time
        print(add_spacing(f"Fetching new candles with start time: {epoch_to_date(new_start_time)}"))

        client = BinanceClient(test=False)  # needed as a connection keeps being reset with same object instance
        new_candles = client.get_klines(startTime=new_start_time)
        if len(new_candles) == 0:
            print(add_spacing("NO new candles found, waiting one minute ..."))
            time.sleep(60)
            bruce_buffer()
            continue

        all_candles.add(new_candles)

        all_candles.shorten()  # shorten candles to past 30 days of data

        # TODO we waste time computing entire dataframe here (should compute only last data point ideally)
        ma_crossover_dataframe = all_candles.create_ma_crossover_dataframe(window_min, window_max, units)
        print("Latest MA crossover data:")
        print(ma_crossover_dataframe.tail())

        suggested_position = all_candles.suggested_position_type(ma_crossover_dataframe)
        current_position = client.get_market_position_type()

        latest_row = ma_crossover_dataframe.iloc[-1]
        if (suggested_position == Side.buy) & (current_position == PositionType.sold):
            # Buy signal + no position on coin. Okay to buy. Make Trade add stop signal.
            notifier.slack_notify(
                f"Buy Signal - Order Executed. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "prod-trades")
        elif (suggested_position == Side.sell) & (current_position == PositionType.bought):
            # Sell signal + position on coin. Okay to sell. Make Trade and clear stop signal.
            notifier.slack_notify(
                f"Sell Signal - Order Executed. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "prod-trades")

        elif (suggested_position == Side.buy) & (
                current_position == PositionType.bought):
            # Buy signal + position on coin. Don't buy more, previous sell missed and stop not hit. Wait for next sell.
            notifier.slack_notify(
                f"Buy Signal - Not Executed. Qty greater than 0 Already. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "prod-trades")
        elif (suggested_position == Side.sell) & (current_position == PositionType.sold):
            # Sell signal + no position on coin. Don't sell and go short. Previous buy missed, wait for the next.
            notifier.slack_notify(
                f"Sell Signal - Not Executed. Qty 0 Already. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "prod-trades")
        else:
            print(add_spacing('No Signal - Do not buy or sell'))
            pass

        current_minutes_value = epoch_to_minutes(new_start_time)
        if current_minutes_value % 10 == 0:  # every 10 minutes save current snapshot
            all_candles.create_crossover_graph(window_min, window_max, units)
            slack_image_upload.upload_current_plot(window_min, window_max, units)
            client.position_summary()
            client.show_open_orders()

        print(add_spacing("Waiting 1 minute for new candles ..."))
        time.sleep(60)
        bruce_buffer()


if __name__ == "__main__":
    notify_ma_crossover(1, 2, units="days")
