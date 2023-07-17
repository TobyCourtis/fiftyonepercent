from datetime import datetime, timedelta
import os
import pickle

from src.client.binance_client import BinanceClient
from src.types.candlesticks import Candlesticks
from src.utils.utils import bruce_buffer, one_minute_as_epoch


def run_back_test():
    '''
    Specify range for candles to be collected from/to
    '''
    days_from = 365
    days_to = None

    filename = f"back_test_output_{datetime.now().strftime('%d_%m_%y_%H_%M')}.txt"
    candles_in_day = 1440

    '''
    Get candles for past 700 days considered entire history of Ethereum
    '''
    candles = get_cache_and_add_to_candles(days=700)  # one time operation with caching

    # shorten number of candles to required range
    candles.shorten(from_limit=(days_from * candles_in_day),
                    to_limit=(days_to * candles_in_day) if days_to is not None else None)
    bruce_buffer()

    strategy_info = f"Backtesting from {get_date_string(days_from)} " \
                    f"until {'now' if days_to is None else get_date_string(days_to)}\n"
    print(strategy_info)
    append_string_to_file(filename, strategy_info)

    units = "days"
    pnl_to_output_str_dict = {}
    for j in range(1, 12):
        for k in range(2, 6):
            buys = 0
            sells = 0
            short_window = j
            long_window = short_window * k
            df = candles.create_ma_crossover_dataframe(short_window, long_window, units=units)
            '''
            For all of our candles - create a MA crossover dataframe of when to buy and sell
            '''
            start_fiat_wallet_value = 200.0
            fiat_wallet = start_fiat_wallet_value
            eth_qty = 0.0

            last_pos = None
            for index, row in df.iterrows():
                '''
                Iterate through the dataframe and buy if BUY signal and SELL if sell

                NB - we begin having no position so if we get immediate sell, do nothing
                NB 2 - We take the current price to be the close price of the latest candle (may not be accurate)
                '''
                if row['Position'] == 1:
                    qty_purchased = fiat_wallet / row['Close']
                    qty_purchased -= qty_purchased * 0.001
                    eth_qty = qty_purchased
                    fiat_wallet = 0.0

                    buys += 1
                    last_pos = 'buy'
                elif row['Position'] == -1:
                    if eth_qty != 0.0:
                        fiat_gained = eth_qty * row['Close']
                        fiat_gained -= fiat_gained * 0.001
                        fiat_wallet = fiat_gained
                        eth_qty = 0.0

                        sells += 1
                        last_pos = 'sell'
            if last_pos is not None:
                """
                 End by selling what we have at market value so we can calculate PNL
                """
                if last_pos == 'buy':
                    last_row = df.iloc[-1]

                    fiat_gained = eth_qty * last_row['Close']
                    fiat_gained -= fiat_gained * 0.001
                    fiat_wallet = fiat_gained
                    eth_qty = 0.0

            PNL = float(fiat_wallet - start_fiat_wallet_value)
            sign = "+++" if PNL > 0 else "---"
            output = f"Units={units}, Short={short_window}, Long={long_window}, Buys={buys}, " \
                     f"Sells={sells}, PNL:{sign}{abs(PNL)}"
            pnl_to_output_str_dict[PNL] = output
            print(output)
            append_string_to_file(filename, output)

    keys = list(pnl_to_output_str_dict.keys())
    keys.sort(reverse=True)
    append_string_to_file(filename, "\nOrdered Output:\n")
    print(f"\nSaving strategies ordered by PnL performance to {filename}\n")
    for key in keys:
        output = pnl_to_output_str_dict[key]
        append_string_to_file(filename, output)

    print("\nFinished backtesting and exited.")


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
        startTime = (datetime.now() - timedelta(**kwargs)).timestamp() * 1000

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
        timeNow = datetime.now().timestamp() * 1000  # acts as endTime in get_klines

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


def get_date_string(days):
    today = datetime.now()
    target_date = today - timedelta(days=days)
    date_string = target_date.strftime("%d-%m-%Y")
    return date_string


def append_string_to_file(filename, new_line_string):
    try:
        with open(filename, 'a') as file:
            file.write(new_line_string + '\n')
    except Exception as e:
        print(f"ERROR writing backtest data to file {filename}")
        print(f"Exception: {e}")


def temp_get_klines():
    client = BinanceClient(test=False)
    candles = client.get_klines(startTime=1675536420001.000)
    return candles


if __name__ == '__main__':
    # get_cache_and_add_to_candles(days=701)  # 1008 calls gathers all history which only needs to be executed once
    run_back_test()
