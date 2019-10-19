import sqlalchemy

import pandas as pd
import pandas_datareader.data as web
from datetime import datetime

import config
import helpers

date_format = '%Y-%m-%d %H:%M:%S'

class DataAccess:
    def __init__(self, file_name):
        """Each thread should have its own DataAccess object to avoid race conditions.
        Also: Each DataAccess object gets its own file to avoid race conditions in multithreading"""
        sqlite_file = f'sqlite:///data/{file_name}.sqlite'
        self.database = sqlalchemy.create_engine(sqlite_file)

    def write_to_db(self, df, symbol):
        """Writes a pandas.DataFrame to sql."""
        print(f'{symbol}: Writing {df.shape[0]} dates to database', flush=True)
        df.index.names = ['Date']
        df.to_sql(self.sql_friendly_symbol(symbol), self.database, index=True, if_exists='replace')

    def get_df_from_db(self, symbol):
        """Fetches a Symbol from the DB. Returns None if not available."""
        df = None
        try:
            print(f'{symbol}: Getting from DB', flush=True)
            df = pd.read_sql('select * from ' + self.sql_friendly_symbol(symbol), self.database, index_col='Date', parse_dates='Date')
            print(f'{symbol}: is in DB.', flush=True)
        except (sqlalchemy.exc.OperationalError, KeyError):
            print(f'{symbol}: not in DB.', flush=True)
        return df

    def get_df_from_remote(self, symbol, start_date, end_date, source):
        """Fetches the symbol from the given remote source.\n
        Sources can be (so far):\n
        - quandl
        - stooq
        - iex"""
        try:
            print(f'{symbol}: Fetching from. Start: {start_date}. End: {end_date}. Source: {source}', flush=True)
            if source == 'quandl':
                df = web.DataReader(symbol, source, start=start_date, end=end_date, api_key=config.data_quandl_api_key)
            elif source == 'stooq':
                df = web.DataReader(symbol, source, start=start_date, end=end_date)
            elif source == 'iex':
                df = web.DataReader(symbol, source, start=start_date, end=end_date)
            else:
                raise "Specified Unknown remote source"
        except Exception as e:
            print(f'{symbol}: Returning empty dataframe for {symbol}. Cause: {e}', flush=True)
            return pd.DataFrame()
        return df

    def get_df(self, symbol, start_date, end_date, source):
        """This function is intended to use a DB as cache for dataframes so we don't
        always need to fetch everything anew."""
        print(f'{symbol}: Getting data. Start: {start_date}. End: {end_date}. Source: {source}', flush=True)

        df = None
        df_is_new = False
        missing_df = None
        # 1. Try get from DB. If available, see if we need to fetch data for missing dates
        df = self.get_df_from_db(symbol)
        if (not df is None):
            if (df.index.is_monotonic_increasing):
                df = df.iloc[::-1]
            last_db_date_object = df.index[0]
            print(f'{symbol}: Last date in DB: {last_db_date_object}', flush=True)
            desired_last_date_object = datetime.strptime(end_date, '%Y-%m-%d')
            date_delta_in_days = abs((last_db_date_object - desired_last_date_object).days)
            print (f'{symbol}: Date delta: {date_delta_in_days}')
            # 1.1. If we miss dates fetch them and add to df
            if (date_delta_in_days > 1):
                new_start_date = helpers.get_date_in_the_past(date_delta_in_days - 1)
                print(f'{symbol}: Fetching values since {new_start_date}.', flush=True)
                missing_df = self.get_df_from_remote(symbol, new_start_date, end_date, source)
                print(f'{symbol}: Fetched {missing_df.shape[0]} dates', flush=True)
                if (missing_df.size > 0):
                    df = df.combine_first(missing_df)
                    # For some reason combine_first is reversing the order
                    if (missing_df.index.is_monotonic_increasing):
                        df = df.iloc[::-1]

        # 2. If not available in DB, get data from remote:
        # - Either The df is empty and does not contain a 'Date' column. 
        # - Or the Symbol could not be found in the database at all.
        else:
            print(f'{symbol}: Retrieving complete series from remote.', flush=True)
            df = self.get_df_from_remote(symbol, start_date, end_date, source)
            if (df.index.is_monotonic_increasing):
                df = df.iloc[::-1]
            df_is_new = True

        # 3. Write new values to DB
        # Only write if not yet in DB
        if (not df_is_new and not missing_df is None and missing_df.size > 0):
            print (f'{symbol}: Known symbol. Updating stored values with missing dates.', flush=True)
            missing_df = df.drop(columns=['Open', 'High', 'Low', 'Change', 'Turnover', 'TradedVolume', 'LastPriceoftheDay', 'DailyTradedUnits', 'DailyTurnover', 'open', 'high', 'low', 'volume'], errors='ignore')
            self.write_to_db(missing_df, symbol)
        elif (df_is_new and not df is None and df.size > 0):
            print (f'{symbol}: New symbol. Need to store everything.', flush=True)
            df = df.drop(columns=['Open', 'High', 'Low', 'Change', 'Turnover', 'TradedVolume', 'LastPriceoftheDay', 'DailyTradedUnits', 'DailyTurnover', 'open', 'high', 'low', 'volume'], errors='ignore')
            self.write_to_db(df, symbol)

        return df

    def sql_friendly_symbol(self, symbol):
        return symbol.replace('/', '')

    def latest_date(self, df):
        return df['Date'].get_values()[0]