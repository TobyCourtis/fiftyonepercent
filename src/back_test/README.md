# Backtesting V1

## Approach

1. Get cached Candlesticks from candlestick_history.pkl if present
2. Update cache with latest candles if required
3. Gathers 700 days of candlesticks to roughly mid 2021 (avoiding initial massive surge in price of ETH from mid 2020 to
   2021)
4. Loops through short window 1 to 11. Large window = short * X where X is 2 to 5. Runs with units hours and days.
5. Begins computing PnL for the 700 days
   1. Begins with no position and will begin trading from first buy signal
   2. Ends with final SELL if position ended on a buy
6. Writes findings to stdout and a file of current date w/ hours and minute

## Considerations !

V1 of the backtesting does not factor in the fees in regard to buying and selling on the Binance Exchange.
This should be factored in when deciding a strategy. For now, we lent towards a strategy that trades more conservatively
to avoid losses from the high fee percentage.

## TODO

- Incorporate fees into the testing
- Run backtesting against randomly generated exchange history. Ideally net-zero volatility so we know the bot makes
  money in a flat market.
- Test ending on a sell functions correctly

