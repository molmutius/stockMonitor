from pandas_datareader import data
import pandas_datareader.data as web
from matplotlib import pyplot as plot
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from enum import Enum

import technical_indicators as technical_indicators

class Stock:
    """
    This class represents a stock with access to its prices and derived indicators
    \n
    Constructor Params:\n
    days    -- number of days to look at beginning from today\n
    name    -- real name of the stock\n
    symbol  -- the symbolic representation of this stock will be used to get the data\n
    """

    QUANDL_API_KEY = 'y-owmY6P2z8EpzQyNL53'
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')

    def __init__(self, days, name, symbol):
        self.days = days
        self.name = name
        self.symbol = symbol
        self.df = self.get_stock_data()
        if (self.df.size > 0):
            self.has_enough_data = True
        else:
            self.has_enough_data = False

    def get_past_date(self, days):
        '''Returns date x days in the past from today'''
        return datetime.strftime(datetime.now() - timedelta(days), '%Y-%m-%d')

    def get_stock_data(self):
        """
        Returns the given symbol as panda dataframe\n
        \n
        Params:\n
        days -- number of days to get counting backwards from today
        """
        print('Getting data for ' + self.symbol + ' [Source: Quandl]')
        past_date = self.get_past_date(self.days)
        df = web.DataReader(self.symbol, 'quandl', start=past_date, end=self.today, access_key=self.QUANDL_API_KEY)
        return df

    def get_closing_prices(self, df):
        """
        Get panda time series of closing prices for given DF. Only consider business days.
        """
        close = df['Close']
        past_date = self.get_past_date(self.days)
        all_weekdays = pd.date_range(start=past_date, end=self.today, freq='B')
        close = close.reindex(all_weekdays)
        # Fills N/A with last known value
        close = close.fillna(method='ffill')
        return close

    def get_latest_rsi(self):
        '''Returns latest RSI value, calculates RSI history first if necessary'''
        if (not self.has_enough_data):
            print('Not enough data to calculate RSI for ' + self.symbol)
            return -1
        try:
            if ('RSI14' not in self.df.columns):
                closings = self.get_closing_prices(self.df)
                self.df = technical_indicators.get_rsi(self.symbol, self.df, closings, 14)
            last_rsi = self.df['RSI14'].iloc[0]
            return last_rsi
        except KeyError:
            print('Could not determine RSI for ' + self.symbol)
            return -1

    def draw_plot(self, indicators):
        """
        Draws a plot of the given dataframe and the desired indicators. RSI is always plotted.

        params:
        indicators -- list of technical_indicators.Indicators to draw addionally
        """
        prices = self.get_closing_prices(self.df)
        fig, ax = plot.subplots(2, 1, constrained_layout=True, figsize=(16,9))
        ax[0].plot(prices.index, prices, label=self.symbol)

        self.df = technical_indicators.get_sma(self.df, prices, 10)
        self.df = technical_indicators.get_ema(self.df, prices, 10)
        # TODO: Extend here for more indicators to plot

        # Price and general Indicators
        for column in self.df.columns:
            for indicator in technical_indicators.Indicators:
                if (str(column) == str(indicator.name) and indicator.name is not technical_indicators.Indicators.RSI14.name):
                    values = self.df[column]
                    ax[0].plot(values.index, values, label=column)

        ax[0].set_xlabel('Date')
        ax[0].set_ylabel('Closing price')
        ax[0].legend()

        # RSI indicator
        rsi14 = self.df['RSI14']
        ax[1].set_xlabel('Date')
        ax[1].set_ylabel('Relative Strength Index')
        ax[1].set_ylim([0, 100])
        ax[1].plot(rsi14.index, rsi14, label='RSI 14')
        ax[1].hlines(30, self.get_past_date(self.days), self.today, linestyles='dotted')
        ax[1].hlines(70, self.get_past_date(self.days), self.today, linestyles='dotted')

        plot.show()
