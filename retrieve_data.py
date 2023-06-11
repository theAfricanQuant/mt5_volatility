
#
# (c) Ricky Macharm, MScFE
# https://SisengAI.com
#

"""This is for all the code used to interact with Hantec data and the SQLite database. 
The whole setup relies on our account number, password and server details
stored in our `.env` file and imported via the `config` module.
"""

import sqlite3

import pandas as pd
import requests
from config import settings
import MetaTrader5 as mt
from tabulate import tabulate


class MT5_Data:
    
    """Class to get the desired trading instrument from any broker that offers mt5 and the 
        features of 'open', 'high', 'low', 'close' & 'tick_volume' arranged in a convenient 
        fashion in a DataFrame.
    """
    
    def __init__(self, login=settings.login, password=settings.password, server=settings.server):
        self.__login = login
        self.__password = password
        self.__server = server  
        
        
        
    def ticker_data(self, ticker, time_frame="D1", start_bar = 0, num_bars = 99999):
    
        """Code to retrieve ticker data from your broker.
        
        Parameters
        ----------
        ticker : str
            The ticker symbol of the FOREX pair, Stock or CFD. To see the list of available tickers
            or symbols, run the `ticker_list` method
        time_frame: str
            The desired time frame of the instrument. By default its set to "D1" 
            or daily bars. You have the option to set it to "M1", "M2", "M3", "M5",
            "M10", "M15", "M30", "H1", "H2", "H3", "H4", "H6", "H8", "H12", "D1",
            "W1", "MN1"
        start_bar : int
            initial bar index. Set to 0 by default.
            
        num_bars : int
            Total number of bars to fetched. Set to 99999 by default. Works even if the available bars are
            less.
        

        Returns
        -------
        pd.DataFrame
            Columns are 'open', 'high', 'low', 'close', and 'tick_volume'.
            'tick_volume' is set to integer, the rest are all set to float.        
        
        """
        
         # intialize the mt5 account
        mt.initialize()
 
        # log in to a trading account of your broker
        mt.login(self.__login, self.__password, self.__server)

        if ticker not in [s.name for s in mt.symbols_get()]:
                    raise Exception(
                        f"Invalid Ticker name. {self.__server} does not contain '{ticker}'."
                    )

        timeframe = eval(f'mt.TIMEFRAME_{time_frame}') # to remove the quotation marks
        bars = mt.copy_rates_from_pos(ticker, timeframe, start_bar, num_bars)

        return (pd.DataFrame(bars)
             .assign(date = lambda x: 
                     pd.to_datetime(x['time'], unit='s'))
             .drop(['spread', 'real_volume', 'time'], axis=1)
             #.pipe(lambda x: x.loc[x.tick_volume > 10])
             .set_index('date')
            )  
    
    
    def ticker_list(self):
        
        mt.initialize()
        mt.login(self.__login, self.__password, self.__server)
        tl = [s.name for s in mt.symbols_get()]
        out_put = [tl[i: i+14] for i in range(0, len(tl), 14)]
        
        return print(tabulate(out_put, tablefmt="grid"))
    
    
class SQLiteRepo:
    def __init__(self,
                connection):
        self.connection = connection

    def insert_table(self, table_name,
                    records, if_exists="fail"):
        
    
        """Create a SQLite database & Insert DataFrame as table

        Parameters
        ----------
        table_name : str
            in this case we use the ticker symbol as table name.
        records : pd.DataFrame
        if_exists : str, optional
            How to behave if the table already exists.

            - 'fail': Raise a ValueError.
            - 'replace': Drop the table before inserting new values.
            - 'append': Insert new values to the existing table at the bottom.

            Dafault: 'fail' so we don't mistakenly overwrite our previously
            stored data.

        Returns
        -------
        dict
            Dictionary has two keys:

            - 'transaction_successful', followed by bool (True or False)
            - 'records_inserted', followed by int (for the number of records updated)
        """
        
        n_inserted = (records.sort_index(ascending=False)
                      .to_sql(name=table_name,
                       con=self.connection,
                       if_exists=if_exists))
        
        return {
            "transaction_successful":True,
            "records_inserted": n_inserted
        }

    def read_table(self, table_name, limit=None):
    
        """Read table from database.

        Parameters
        ----------
        table_name : str
            Name of table in SQLite database.
        limit : int, None, optional
            Number of most recent records to retrieve. If `None`, all
            records are retrieved. By default, `None`.

        Returns
        -------
        pd.DataFrame
            Index is DatetimeIndex "date". Columns are 'open', 'high',
            'low', 'close', and 'volume'. All columns are numeric.
        """
        # Create SQL query (with optional limit)
        if limit:
            sql = f"SELECT * FROM '{table_name}' LIMIT {limit}"
        else:
            sql = f"SELECT * FROM '{table_name}'"


        # Retrieve data, read into DataFrame & Return DataFrame
        return  pd.read_sql(
                sql=sql,
                con=self.connection,
                parse_dates=["date"],
                index_col="date"
                ).sort_index(ascending=True)
