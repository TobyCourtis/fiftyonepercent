import datetime
import os
import pickle

from src.client.binance_client import BinanceClient
from src.types.candlesticks import Candlesticks
from src.utils.utils import bruce_buffer, one_minute_as_epoch


def run_back_test():
    days_from = 699
    days_to = None
    duration = 699 - (days_to if days_to is not None else 0)

    candles_in_day = 1440

    candles = get_cache_and_add_to_candles(days=700)

    print(f"Length: {len(candles)}")
    candles.shorten(from_limit=(days_from * candles_in_day),
                    to_limit=(days_to * candles_in_day) if days_to is not None else None)
    print(f"Length: {len(candles)}")
    bruce_buffer()

    print(
        f"PNL for {duration} days starting {days_from} days ago"
        f" {f'ending {days_to} days ago ' if days_to is not None else ''}using different strategies:")
    for i in range(2):
        if i == 0:
            units = "hours"
        else:
            units = "days"
        for j in range(1, 12):
            for k in range(2, 6):
                buys = 0
                sells = 0
                short_window = j
                long_window = short_window * k
                df = candles.create_ma_crossover_dataframe(short_window, long_window, units=units)
                PNL = None
                last_pos = None
                for index, row in df.iterrows():
                    if row['Position'] == 1:
                        if PNL is None:
                            PNL = 0
                        PNL -= row['Close']  # minus buys
                        buys += 1
                        last_pos = 'buy'
                    elif row['Position'] == -1:
                        if PNL is not None:
                            PNL += row['Close']  # add the sells
                            sells += 1
                            last_pos = 'sell'
                # end by selling at current value?
                if last_pos is not None:
                    if last_pos == 'buy':
                        # fake sell
                        last_row = df.iloc[-1]
                        PNL += last_row['Close']  # add a final sell to sort PNL

                print(f"Units={units}, Short={short_window}, Long={long_window}, Buys={buys}, Sells={sells}, PNL={PNL}")


def save_candle_history(candles: Candlesticks):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = f'{current_dir}/candlestick_history.pkl'
    with open(file_path, 'wb') as file:
        pickle.dump(candles, file)
    print(f"Saved candle history to: {file_path}. Length={len(candles)}")


def read_candle_history():
    all_candle_history = Candlesticks()
    try:
        with open(f'candlestick_history.pkl', 'rb') as file:
            all_candle_history = pickle.load(file)
        print(f"Read candle history of length: {len(all_candle_history)}")
        return all_candle_history
    except FileNotFoundError:
        print("No history found, fetching now.")
        return None


def get_cache_and_add_to_candles(**kwargs):
    client = BinanceClient(test=False)

    # 1. get history
    all_candle_history: Candlesticks = read_candle_history()

    # 2. get required start time
    if "startTime" in kwargs:
        startTime = kwargs['startTime']
    else:
        startTime = (datetime.datetime.now() - datetime.timedelta(**kwargs)).timestamp() * 1000

    # 3. get important history data (start and end times)
    if all_candle_history is not None:
        """
        The usage of the below variables is important.
        
        Open time = 00:47:00 (47m)
        Close time = 00:47:59.999
        
        Inputting 47:00 into get_klines returns first candle starting openTime 47:00
        Inputting 47:01 into get_klines returns first candle strating openTime 48:00
        
        Each check done is very specific to fetching 
        """
        history_first_open_time = all_candle_history.openTime[0]
        history_first_close_time = all_candle_history.closeTime[0]
        history_end_open_time = all_candle_history.openTime[-1]
        history_end_close_time = all_candle_history.closeTime[-1]

    # 4. Check if history exists and if the required new startTime is within the candlestick history
    # add on 1second to start time to account for when you first getCandles() the close time of the returned candle
    # is startTime to the next WHOLE minutes (so it's simple here just to add on 1 minute)
    if all_candle_history is not None and (startTime + one_minute_as_epoch) >= history_first_open_time:
        """
        START TIME WITHIN HISTORY SO ONLY FETCHING NEW CANDLES
        """
        timeNow = datetime.datetime.now().timestamp() * 1000  # acts as endTime in get_klines

        # check if candle history is already up-to-date
        if timeNow < history_end_close_time:
            print("Do not fetch any more candles. History is up to date")
            return all_candle_history
        else:
            # fetch only the new candles to append to the history
            new_candles = client.get_klines(startTime=(history_end_open_time + one_minute_as_epoch))
            if len(new_candles) != 0:
                all_candle_history.add(new_candles)
                save_candle_history(all_candle_history)
                return all_candle_history
            else:
                print("Candle history is already up to date. Case 2. (shouldn't really reach here)")
    else:
        """
        START TIME BEFORE HISTORY SO FETCHING AND SAVING EVERYTHING FROM START TO NOW. 
        """
        print('* FETCHING NEW HISTORY *')
        new_candle_history = client.get_klines(**kwargs)
        save_candle_history(new_candle_history)
        return new_candle_history


def temp_get_klines():
    client = BinanceClient(test=False)
    candles = client.get_klines(startTime=1675536420001.000)
    return candles


if __name__ == '__main__':
    # get_cache_and_add_to_candles(days=701)  # 1008 calls, all history
    run_back_test()
