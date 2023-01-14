from pprint import pprint


class Candlesticks:
    """
    NB: This data type stores many and not singular candlesticks

    Candlestick type derived from API: https://binance-docs.github.io/apidocs/#kline-candlestick-data
    """

    def __init__(self, **kwargs):
        self.openTime = []
        self.open = []
        self.high = []
        self.low = []
        self.close = []
        self.volume = []
        self.closeTime = []
        self.quoteAssetVolume = []
        self.numberOfTrades = []
        self.takerBuyBaseAssetVolume = []
        self.takerBuyQuoteAssetVolume = []
        self.ignore = []

    def display_data(self):
        print(self.openTime)
        pprint(vars(self))


if __name__ == "__main__":
    foo = Candlesticks()
    foo.display_data()
