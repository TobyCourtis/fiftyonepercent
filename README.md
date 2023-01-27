# fiftyonepercent


## Description
Algorithmic crypto trading project using the Binance exchange

This project features a main Python file housing a "BinanceClient" class which allows the following in test OR prod envs:
- Place trades
- Pulling of market data (which can be plotted to a graph)
- Retrieve user wallet/account information
- Helper functions for manipulation of market data


## External Docs
[Binance API Documentation](https://binance-docs.github.io/apidocs)


## Dependencies
All dependencies should be included in the requirements.txt file

`python3 -m pip install -r requirements.txt`

## Running locally
It is recommended to run the following to allow running as a module globally in the terminal:

`export PYTHONPATH="${PYTHONPATH}:/home/users/your_user/fiftyonepercent"`

This will allow the following to be executed globally:

`python3.10 -m clients.live_ma_crossover_notifier`

## Testing

`cd src && python3 -m unittest`