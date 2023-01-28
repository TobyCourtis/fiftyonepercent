import time

from helpers import convert_to_hours, epoch_to_date, bruce_buffer
from binance_client import BinanceClient
from src.notify.notifier import slack_notify


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

    # initialise candles
    _, window_max_in_hours = convert_to_hours(window_min, window_max, units)
    all_candles = client.get_klines(hours=window_max_in_hours)

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

        if position == 1:
            print('\n!notify buy!\n')
            latest_row = ma_crossover_dataframe.iloc[-1]
            slack_notify(
                f"Buy buy buy. Time={latest_row.name}, Short={latest_row['Short']}, Long={latest_row['Long']}, "
                f"windowMin={window_min}, windowMax={window_max}, units={units}", "crypto-trading")
        elif position == -1:
            print('\nnotify sell\n')
            latest_row = ma_crossover_dataframe.iloc[-1]
            slack_notify(
                f"Sell sell sell. Time={latest_row.name}, Short={latest_row['Short']}, Long={latest_row['Long']}, "
                f"windowMin={window_min}, windowMax={window_max}, units={units}", "crypto-trading")
        else:
            print('\nDo not buy or sell\n')
            pass

        # TODO every 10 minutes send photo of graph to slack

        # TODO breakpoints or fetch times could cause the wait to be more than 1 minute
        #  if multiple candles have been released then we need to check all of the
        #  corresponding ma_crossover_dataframe rows for 'Position' buy or sell

        print("\nWaiting 1 minute for new candles ...")
        time.sleep(60)
        print("...Done waiting\n")

        bruce_buffer()


if __name__ == "__main__":
    notify_ma_crossover(2, 4, units="days")
