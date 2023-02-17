import sys
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from src.client.binance_client import BinanceClient
from src.utils.utils import epoch_to_date, epoch_to_minutes, add_spacing, PositionType, Side, LastNotifiedState
from src.utils.ma_crossover_utils import send_update_snapshot, buy, sell, \
    sleep_until_next_candle_released


def notify_ma_crossover(window_min, window_max, units, test=True):
    """

    Main function to notify in the case of a MA crossover.
    - Gets as many candles as required for window_max
    - Keeps fetching each minute for new 1m interval candles
    - Generates dataframe for current candles
    - Notifies if position is buy or sell (also prints tail of current dataframe)

    :param test: Test env (True) or prod env (False)
    :param window_min:  Short window size
    :param window_max:  Long window size
    :param units: units of window_min/max in days or hours
    :return: (void) Notifies if we should buy or sell and executes
    """
    client = BinanceClient(test=test)

    # initialise 30 days of candles
    all_candles = client.get_klines(days=30)

    last_notified_state = LastNotifiedState.un_notified

    while True:
        new_start_time = all_candles.closeTime[-1]  # start from last candle closing time
        print(add_spacing(f"Fetching new candles with start time: {epoch_to_date(new_start_time)}"))

        client = BinanceClient(test=test)  # needed as a connection keeps being reset with same object instance
        new_candles = client.get_klines(startTime=new_start_time)
        if len(new_candles) == 0:
            print(add_spacing("No new candles found. Sleeping."))
            sleep_until_next_candle_released(new_start_time)
            continue

        all_candles.add(new_candles)

        all_candles.shorten()  # shorten candles to past 30 days of data

        # TODO we waste time computing entire dataframe here (should compute only last data point ideally)
        ma_crossover_dataframe = all_candles.create_ma_crossover_dataframe(window_min, window_max, units)
        print("Latest MA crossover data:")
        print(ma_crossover_dataframe.tail())

        suggested_position = all_candles.suggested_position_type(ma_crossover_dataframe)
        current_position = client.get_account_balance_position_type(include_locked=True)

        latest_row = ma_crossover_dataframe.iloc[-1]

        print(add_spacing(f"Current position: {current_position}. Suggested position: {suggested_position}"))
        if (suggested_position == Side.buy) & (current_position == PositionType.sold):
            """
            BUY
            """
            buy(window_min, window_max, units, latest_row, client)
            last_notified_state = LastNotifiedState.un_notified

        elif (suggested_position == Side.sell) & (current_position == PositionType.bought):
            """
            SELL
            """
            sell(window_min, window_max, units, latest_row, client)
            last_notified_state = LastNotifiedState.un_notified

        elif (suggested_position == Side.buy) & (current_position == PositionType.bought):
            """
            AVOIDING REPEAT BUY
            """
            symbol_qty = client.account_balance_by_symbol(include_locked=True)
            if last_notified_state != LastNotifiedState.avoid_repeat_buy:
                print(f"Buy signal not executed. Symbol quantity is greater than 0 ({round(symbol_qty, 8)})")
                last_notified_state = LastNotifiedState.avoid_repeat_buy

        elif (suggested_position == Side.sell) & (current_position == PositionType.sold):
            """
            AVOIDING REPEAT SELL
            """
            symbol_qty = client.account_balance_by_symbol(include_locked=True)
            if last_notified_state != LastNotifiedState.avoid_repeat_sell:
                print(f"Sell signal not executed. Symbol quantity already 0 ({round(symbol_qty, 8)})")
                last_notified_state = LastNotifiedState.avoid_repeat_sell

        else:
            print(add_spacing('Suggested position is to hold. Doing nothing.'))

        current_minutes_value = epoch_to_minutes(new_start_time)
        if current_minutes_value % 10 == 0:  # every 10 minutes save current snapshot
            send_update_snapshot(all_candles, client, window_min, window_max, units)

        sleep_until_next_candle_released(new_start_time)


if __name__ == "__main__":
    notify_ma_crossover(6, 12, units="days", test=False)
