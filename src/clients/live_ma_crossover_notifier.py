import time

from binance_client import BinanceClient
from helpers import epoch_to_date, epoch_to_minutes, bruce_buffer
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
        print(f"\nFetching new candles with start time: {epoch_to_date(new_start_time)}\n")

        client = BinanceClient(test=False)  # needed as a connection keeps being reset with same object instance
        new_candles = client.get_klines(startTime=new_start_time)
        if len(new_candles) == 0:
            print("\nNO new candles found, waiting one minute ...")
            time.sleep(60)
            print("...Done waiting\n")
            bruce_buffer()
            continue

        all_candles.add(new_candles)

        all_candles.shorten()  # shorten candles to past 30 days of data

        # TODO we waste time computing entire dataframe everytime candles are added, functionality just to compute
        #  the newest data point would be optimal
        ma_crossover_dataframe = all_candles.create_ma_crossover_dataframe(window_min, window_max, units)
        print("\nLatest MA crossover data:")
        print(ma_crossover_dataframe.tail())
        print("\n")

        position = all_candles.get_current_position(ma_crossover_dataframe)
        qty = client.get_market_position()

        print(f"\nCurrent qty: {qty}")
        print("\n")

        latest_row = ma_crossover_dataframe.iloc[-1]
        if (position == 1) & (qty == 0):
            # Buy signal + no position on coin. Okay to buy. Make Trade add stop signal.
            notifier.slack_notify(
                f"Buy Signal - Order Executed. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "crypto-trading")
        elif (position == -1) & (qty > 0):
            # Sell signal + position on coin. Okay to sell. Make Trade and clear stop signal.
            notifier.slack_notify(
                f"Sell Signal - Order Executed. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "crypto-trading")

        elif (position == 1) & (qty > 0.0005):
            # Buy signal + position on coin. Don't buy more, previous sell missed and stop not hit. Wait for next sell.
            notifier.slack_notify(
                f"Buy Signal - Not Executed. Qty greater than 0 Already. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "crypto-trading")
        elif (position == -1) & (qty == 0):
            # Sell signal + no position on coin. Don't sell and go short. Previous buy missed, wait for the next.
            notifier.slack_notify(
                f"Sell Signal - Not Executed. Qty 0 Already. "
                f"Time={latest_row.name}, "
                f"Short={latest_row['Short']}, "
                f"Long={latest_row['Long']}, "
                f"windowMin={window_min}, "
                f"windowMax={window_max}, "
                f"units={units}",
                "crypto-trading")
        else:
            print('\nNo Signal - Do not buy or sell\n')
            pass

        current_minutes_value = epoch_to_minutes(new_start_time)

        if current_minutes_value % 10 == 0:  # every 10 minutes save current snapshot
            all_candles.create_crossover_graph(window_min, window_max, units)
            slack_image_upload.upload_current_plot(window_min, window_max, units)
            client.position_summary()
            client.show_open_orders()

        # TODO every 10 minutes send photo of graph to slack

        # TODO breakpoints or fetch times could cause the wait to be more than 1 minute
        #  if multiple candles have been released then we need to check all of the
        #  corresponding ma_crossover_dataframe rows for 'Position' buy or sell

        print("\nWaiting 1 minute for new candles ...")
        time.sleep(60)
        print("...Done waiting\n")

        bruce_buffer()


if __name__ == "__main__":
    notify_ma_crossover(1, 2, units="days")
