
#
# (c) Ricky Macharm, MScFE
# https://SisengAI.com
#



import numpy as np
import pandas as pd
from config import settings
import MetaTrader5 as mt



mt.initialize()
 
# log in to trading account
mt.login(settings.login, settings.password, settings.server)

def get_data(ticker, tf="D1", start_bar = 0, num_bars = 99999):
    
    """Code to get the desired trading instrument, time frame and the 
    features of 'open', 'high', 'low' and 'close ' arranged in a convenient fashion
    from the mt5 platform and returned as a DataFrame"""
    
    timeframe = eval(f'mt.TIMEFRAME_{tf}') # to remove the quotation marks
    bars = mt.copy_rates_from_pos(ticker, timeframe, start_bar, num_bars)
        
    return (pd.DataFrame(bars)
         .assign(date = lambda x: 
                 pd.to_datetime(x['time'], unit='s'))
         .drop(['spread', 'real_volume', 'time'], axis=1)    
         .set_index('date')
        )  
    
tickers = ['AUDUSD', 'EURJPY', 'EURUSD', 'GBPJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'USDJPY', 
        'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD',
        'EURCAD', 'EURCHF', 'EURGBP', 'EURNZD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPNZD', 'US500',
        'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'XAUUSD', 'US30',  'US100', 'GER40', 'UK100',]
    
