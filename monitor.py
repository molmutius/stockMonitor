from pandas_datareader import data
import pandas_datareader.data as web
from matplotlib import pyplot as plot
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from enum import Enum

QUANDL_API_KEY = 'y-owmY6P2z8EpzQyNL53'
today = datetime.strftime(datetime.now(), '%Y-%m-%d')

class Indicators(Enum):
    """
    Extend/narrow this enum to consider less indicators
    """
    RSI14 = 1
    EMA10 = 2
    SMA10 = 3
    EMA100 = 4

def get_past_date(days):
    '''Returns date x days in the past from today'''
    return datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%d')

def get_stock(symbol, days):
    """
    Returns the given symbol as panda dataframe

    Params:
    symbol -- the symbol to query
    days -- number of days to get counting backwards from today
    """
    past_date = get_past_date(days)
    df = web.DataReader(symbol, 'quandl', start=past_date, end=today, access_key=QUANDL_API_KEY)
    return df

def get_closing_prices(df, days):
    """
    Get panda time series of closing prices for given DF
    """
    close = df['Close']
    past_date = get_past_date(days)
    all_weekdays = pd.date_range(start=past_date, end=today, freq='B')
    close = close.reindex(all_weekdays)
    close = close.fillna(method='ffill')
    return close

def get_sma(prices, period):
    """
    Gets the simple moving average for the given pandas price series
    
    Params:
    prices -- panda series holding the prices
    period -- average over that many days
    """
    if (prices.size < period):
        raise ValueError('Series too short for intended rolling avg')
    return prices.rolling(window=period).mean()

def get_ema(prices, period):
    """
    Gets the exponential moving average for the given pandas price series
    
    Params:
    prices -- panda series holding the prices
    period -- average over that many days
    """
    if (prices.size < period):
        raise ValueError('Series too short for intended rolling avg')
    return pd.Series.ewm(prices, span=period).mean()

def get_rsi(series, period=14):
    """
    Gets the exponential moving average for the given pandas price series
    
    Params:
    prices -- panda series holding the prices
    period -- average over that many days
    """
    delta = series.diff().dropna()

    up = delta * 0
    down = up.copy()

    up[delta > 0] = delta[delta > 0]
    down[delta < 0] = -delta[delta < 0]

    up[up.index[period]] = np.mean( up[:period] ) #first value is sum of avg gains
    up = up.drop(up.index[:(period)])

    down[down.index[period]] = np.mean( down[:period] ) #first value is sum of avg losses
    down = down.drop(down.index[:(period)])

    rolling_up = up.ewm(com=period).mean()
    rolling_down = down.ewm(com=period).mean()

    rs = rolling_up / rolling_down
    return 100.0 - 100.0 / (1.0 + rs)

def draw_plot(df, symbol):
    """
    Draws a plot of the given dataframe.

    Indicators are added, if they are present in the dataframe and part
    of the Indicators enum.
    """
    prices = get_closing_prices(df, days)
    fig, ax = plot.subplots(figsize=(16,9))
    ax.plot(prices.index, prices, label=symbol)

    #rsi14 = df['RSI14']
    #ax.plot(rsi14.index, rsi14, label='RSI 14')

    for column in df.columns:
        for indicator in Indicators:
            if (column is indicator.name):
                values = df[column]
                ax.plot(values.index, values, label=column)

    ax.set_xlabel('Date')
    ax.set_ylabel('Closing price')
    ax.legend()
    plot.show()


days = 1000
symbol = 'FSE/MOR_X'

# Get the data
df = get_stock(symbol, days)

# Add Indicators to dataframe
closing = get_closing_prices(df, days)
df['RSI14'] = get_rsi(closing)
df['EMA10'] = get_ema(closing, 10)
#df['SMA10'] = get_sma(closing, 10)
df['EMA100'] = get_ema(closing, 100)

# Plot
draw_plot(df, symbol)