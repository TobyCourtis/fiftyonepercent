import psycopg2

from src.client.binance_client import BinanceClient
from src.types.candlesticks import Candlesticks, Candlestick


class CandlestickDbService:
    table_name = "CANDLESTICK"
    postgres_db_info = {
        "host": "0.0.0.0",
        "port": 5438,
        "database": "fiftyonepercent_database",
        "user": "databaseuser",
        "password": "password"
    }

    def __init__(self, table_name=None):
        if table_name:
            self.table_name = table_name
        self.conn = psycopg2.connect(**self.postgres_db_info)

    def insert_candlesticks(self, candles: Candlesticks) -> None:
        batch_cursor = self.conn.cursor()
        candlestick_count = len(candles)
        print(f"Saving {candlestick_count} candles to {self.table_name}.")
        for i in range(candlestick_count):
            candlestick = Candlestick(
                candles.openTime[i],
                candles.open[i],
                candles.high[i],
                candles.low[i],
                candles.close[i],
                candles.volume[i],
                candles.closeTime[i],
                candles.quoteAssetVolume[i],
                candles.numberOfTrades[i],
                candles.takerBuyBaseAssetVolume[i],
                candles.takerBuyQuoteAssetVolume[i],
                candles.ignore[i],
                candles.candleTimeframe  # single timeFrame per Candlesticks object
            )
            self._insert_candlestick(batch_cursor, candlestick)
        print(f"Saved {candlestick_count} candles to {self.table_name}.")
        batch_cursor.close()
        return

    def get_all_candlesticks(self) -> Candlesticks:
        cur = self.conn.cursor()
        query = f"SELECT * FROM {self.table_name}"
        cur.execute(query)
        rows = cur.fetchall()

        candlesticks = Candlesticks()
        for row in rows:
            print(row)
            candlestick = self._convertRowTupleToCandlestick(row)
            candlesticks.append_candlestick(candlestick)
        cur.close()
        return candlesticks

    def _insert_candlestick(self, cursor, candlestick: Candlestick) -> None:
        insert_query = f"INSERT INTO {self.table_name} (openTime, open, high, low, close, volume, closeTime," \
                       f" quoteAssetVolume, numberOfTrades, takerBuyBaseAssetVolume, takerBuyQuoteAssetVolume," \
                       f" ignore, candleTimeframe) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        insert_values = self._build_insert_values(candlestick)
        cursor.execute(insert_query, insert_values)

        self.conn.commit()

    def _build_insert_values(self, candlestick: Candlestick) -> tuple:
        values = (
            candlestick.openTime,
            candlestick.open,
            candlestick.high,
            candlestick.low,
            candlestick.close,
            candlestick.volume,
            candlestick.closeTime,
            candlestick.quoteAssetVolume,
            candlestick.numberOfTrades,
            candlestick.takerBuyBaseAssetVolume,
            candlestick.takerBuyQuoteAssetVolume,
            candlestick.ignore,
            candlestick.candleTimeframe
        )
        return values

    def _convertRowTupleToCandlestick(self, candlestick_db_row_tuple: tuple) -> Candlestick:
        candlestick_db_row_tuple = candlestick_db_row_tuple[1:]  # drop unwanted ID field from row
        return Candlestick(*candlestick_db_row_tuple)


if __name__ == "__main__":
    service = CandlestickDbService()

    client = BinanceClient(test=False)
    candlesticks = client.get_klines(minutes=1)
    # service.insert_candlesticks(candlesticks)
    candles = service.get_all_candlesticks()
    for i in range(len(candles)):
        print(candles.open[i])
        print(candles.openTime[i])
        print(candles.takerBuyBaseAssetVolume[i])
        print(candles.candleTimeframe)
        print(type(candles.open[i]))
        print(type(candles.openTime[i]))
        print(type(candles.takerBuyBaseAssetVolume[i]))
        print(type(candles.candleTimeframe))
