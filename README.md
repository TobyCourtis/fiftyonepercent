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
Due to our import structure you must run this from the project ROOT before using our Python files:

`export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

To verify the project root is in your PYTHONPATH run the following:

`python3.10 -c 'import sys; print(sys.path)' | grep "/fiftyonepercent'"`

## Testing

`cd src && python3 -m unittest`