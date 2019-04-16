import sqlite3
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime

import config
import helpers

date_format = '%Y-%m-%d %H:%M:%S'

class DataAccess:
    def __init__(self):
        self.conn = sqlite3.connect('stock_data.sqlite')

    def write_to_db(self, df, symbol):
        """Writes a pandas.DataFrame to sql.
        TODO: Breaks for some reason when the symbol already exists and the index overlaps
        """
        df.to_sql(self.sql_friendly_symbol(symbol), self.conn, if_exists='replace', index=True)

    def get_df_from_db(self, symbol):
        df = pd.read_sql('select * from ' + self.sql_friendly_symbol(symbol), self.conn)
        return df

    def get_df_witout_db(self, symbol, start_date, end_date):
        df = web.DataReader(symbol, 'quandl', start=start_date, end=end_date, access_key=config.data_quandl_api_key)
        return df

    def get_df(self, symbol, start_date, end_date):
        """
        This function is intended to use a DB as cache for dataframes so we don't
        always need to fetch everything anew.

        TODO: Not yet working because writing to SQL is broken ...
        """
        # 1. Try Get df from DB
        df = None
        try:
            # 2. If available in DB see if we need to fetch data for missing dates
            df = self.get_df_from_db(symbol)
            print(f'{symbol}: is in DB.')
            last_db_date_object = datetime.strptime(df['Date'].iloc[0], date_format)
            desired_last_date_object = datetime.strptime(end_date, '%Y-%m-%d')
            date_delta = abs((last_db_date_object - desired_last_date_object).days)
            # If we miss dates fetch them
            if (date_delta > 0):
                new_start_date = helpers.get_date_in_the_past(date_delta)
                print(f'{symbol}: Fetching values since {new_start_date}.')
                missing_df = web.DataReader(symbol, 'quandl', start=new_start_date, end=end_date, access_key=config.data_quandl_api_key)
                # During weekends there are no new data frames
                if (missing_df.size > 0):
                    df.append(missing_df, ignore_index=False, verify_integrity=True, sort=True)
                    print(df)
        # 3. If not available get from remote
        except pd.io.sql.DatabaseError:
            print(f'{symbol}: not in DB. Checking remote for new data.')
            df = web.DataReader(symbol, 'quandl', start=start_date, end=end_date, access_key=config.data_quandl_api_key)
        
        # 4. Write new values to DB
        try:
            df = df.drop(columns=['Open', 'High', 'Low', 'Change', 'Turnover', 'LastPriceoftheDay', 'DailyTradedUnits', 'DailyTurnover'])
        except KeyError:
            pass
        df.index.name = 'Date'
        self.write_to_db(df, symbol)
        return df

    def sql_friendly_symbol(self, symbol):
        return symbol.replace('/', '')

    def latest_date(self, df):
        return df['Date'].get_values()[0]