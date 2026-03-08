import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_landing_assets_data():
    """
    Fetches 3-month data for BTC, GOLD, SPX500, and NIFTY.
    Returns a dictionary of dataframes.
    """
    assets = {
        'BTCUSD': 'BTC-USD',
        'GOLD': 'GC=F',
        'SPX500': '^GSPC',
        'NIFTY': '^NSEI'
    }
    
    data_results = {}
    
    for name, ticker in assets.items():
        try:
            # Fetch 3 months of daily data
            df = yf.download(ticker, period="3mo", interval="1d")
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                data_results[name] = df
            else:
                data_results[name] = None
        except Exception as e:
            print(f"Error fetching data for {name}: {e}")
            data_results[name] = None
            
    return data_results
