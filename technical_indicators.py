# More indicators: https://github.com/Crypto-toolbox/pandas-technical-indicators/blob/master/technical_indicators.py

import pandas as pd
import numpy as np
from enum import Enum

class Indicators(Enum):
    """
    Extend/narrow this enum to consider less indicators
    """
    RSI14 = 1
    EMA10 = 2
    SMA10 = 3
    EMA100 = 4

def get_rsi(symbol, df, series, period=14):
    """
    Gets the rsi for the given pandas price series
    \n
    Params:\n
    df      -- pandas.dataFrame to which to append to\n
    prices  -- pandas.series holding the prices\n
    period  -- average over that many days, defaults to 14
    """
    if (df.size <= period):
        raise ValueError('Series too short')
    try:
        delta = series.diff().dropna()

        up = delta * 0
        down = up.copy()

        up[delta > 0] = delta[delta > 0]
        down[delta < 0] = -delta[delta < 0]

        up[up.index[period]] = np.mean(up[:period])
        up = up.drop(up.index[:(period)])

        down[down.index[period]] = np.mean(down[:period])
        down = down.drop(down.index[:(period)])

        rolling_up = up.ewm(com=period).mean()
        rolling_down = down.ewm(com=period).mean()

        rs = rolling_up / rolling_down
        rsi = 100.0 - 100.0 / (1.0 + rs)
        rsi_series = pd.Series((rsi), name='RSI' + str(period))

        df = df.join(rsi_series)
        return df
    except IndexError:
        print('Error processing ' + symbol)
        return df
    except ValueError:
        return df

def get_sma(df, prices, period):
    """
    Gets the simple moving average for the given pandas price series\n
    \n
    Params:\n
    prices -- panda series holding the prices
    period -- average over that many days
    """
    if (prices.size < period):
        raise ValueError('Series too short for intended rolling avg')
    sma = pd.Series(prices.rolling(window=period).mean(), name='SMA' + str(period))
    df = df.join(sma)
    return df

def get_ema(df, prices, period):
    """
    Gets the exponential moving average for the given pandas price series\n
    \n
    Params:\n
    prices -- panda series holding the prices
    period -- average over that many days
    """
    if (prices.size < period):
        raise ValueError('Series too short for intended rolling avg')
    ema = pd.Series(prices.ewm(span=period, min_periods=period).mean(), name='EMA' + str(period))
    df = df.join(ema)
    return df