import pickle

from src.client.binance_client import BinanceClient
from src.types.candlesticks import Candlesticks
from src.utils.utils import bruce_buffer


def run_back_test():
    client = BinanceClient(test=False)
    days = 40
    candles = client.get_klines("1m", days=days)
    bruce_buffer()

    print(f"PNL for the past {days} days using different strategies:")
    for j in range(2):
        if j == 0:
            units = "hours"
        else:
            units = "days"
        for i in range(1, 12):
            buys = 0
            sells = 0
            short_window = i
            long_window = short_window * 2
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


def save_candle():
    client = BinanceClient(test=False)
    days = 120
    units = 'days'
    candles = client.get_klines("1m", days=days)
    with open(f'candle_history_{str(days)}_{units}.pkl', 'wb+') as file:
        pickle.dump(candles, file)


def read_candle():
    candles = Candlesticks()
    days = 120
    units = 'days'
    with open(f'candle_history_{str(days)}_{units}.pkl', 'rb+') as file:
        candles = pickle.load(file)
    print(f"I found: {len(candles)} candles")


if __name__ == '__main__':
    read_candle()
