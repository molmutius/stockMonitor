from matplotlib import pyplot as plot
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from enum import Enum

import config
import helpers
import technical_indicators as technical_indicators

class Stock:
    """
    This class represents a stock with access to its prices and derived indicators
    \n
    Constructor Params:\n
    days    -- number of days to look at, beginning from today\n
    name    -- real name of the stock\n
    symbol  -- the symbolic representation of this stock will be used to get the data\n
    data_access -- DataAccess object\n
    df      -- pandas.DataFrame\n
    min_rsi -- send alarm for this stock if below this value\n
    max_rsi -- send alarm for this stock if above this value
    """

    today = datetime.strftime(datetime.now(), '%Y-%m-%d')

    def __init__(self, days, name, symbol, data_access, min_rsi=config.default_min_rsi, max_rsi=config.default_max_rsi):
        self.days = days
        self.name = name
        self.symbol = symbol
        self.data_access = data_access
        self.df = self.get_stock_data()
        self.min_rsi = min_rsi
        self.max_rsi = max_rsi
        if (self.df.size > 0):
            self.has_enough_data = True
        else:
            self.has_enough_data = False

    def get_stock_data(self):
        """
        Fetches this stock as pandas.DataFrame\n
        """
        # QUANDL FSE Data is updated 6:30 pm ET == 00:30 am Berlin
        print('Getting data for ' + self.symbol + ' [Source: Quandl]')
        past_date = helpers.get_date_in_the_past(self.days)
        df = self.data_access.get_df_witout_db(self.symbol, past_date, self.today)
        return df

    def get_closing_prices(self):
        """
        Get panda time series of closing prices for this stock. Only consider business days.
        """
        close = self.df['Close']
        past_date = helpers.get_date_in_the_past(self.days)
        all_weekdays = pd.date_range(start=past_date, end=self.today, freq='B')
        close = close.reindex(all_weekdays)
        # Fills N/A with last known value
        close = close.fillna(method='ffill')
        return close

    def get_latest_rsi(self):
        """
        Returns latest RSI value, calculates RSI history first if necessary. 
        Returns -1 in case calculation is impossible.
        """
        if (not self.has_enough_data):
            print('Not enough data to calculate RSI for ' + self.symbol)
            return -1
        try:
            if ('RSI14' not in self.df.columns):
                closings = self.get_closing_prices()
                self.df = technical_indicators.get_rsi(self.symbol, self.df, closings, 14)
            last_rsi = self.df['RSI14'].iloc[0]
            return last_rsi
        except KeyError:
            print('Could not determine RSI for ' + self.symbol)
            return -1

    # This approach breaks when RSI oscilates between the 2 thresholds in 2 consecutive intervals.
    # For the sake of simplicity, we don't handle that case here.
    def get_rsi_exceeded_since_date(self):
        '''Gets the date since when RSI thresholds are exceeded'''
        # Create boolean mask of exceed yes/no and filter df with it
        above = self.df['RSI14'] >= self.max_rsi
        below = self.df['RSI14'] <= self.min_rsi
        exceed_mask = above | below
        # Get date of the first index before today where the threshold is not exceeded
        first_date_not_exceeded = self.df[exceed_mask.eq(0)].index[0]
        return first_date_not_exceeded

    def draw_plot(self, indicators):
        """
        Draws a plot of the given dataframe and the desired indicators. RSI is always plotted.

        params:
        indicators -- list of technical_indicators.Indicators to draw addionally
        """
        prices = self.get_closing_prices()
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
        past_date = helpers.get_date_in_the_past(self.days)
        ax[1].hlines(30, past_date, self.today, linestyles='dotted')
        ax[1].hlines(70, past_date, self.today, linestyles='dotted')

        plot.show()
