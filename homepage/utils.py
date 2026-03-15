import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

# Create cache directory if it doesn't exist to prevent yfinance OperationalError
cache_dir = os.path.join(os.getcwd(), 'ml', 'cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
# yf.set_tz_cache_location(cache_dir)

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
            # Fetch 1 month of daily data
            tkr = yf.Ticker(ticker)
            df = tkr.history(period="1mo", interval="1d")
            
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                data_results[name] = df
            else:
                print(f"No data for {name}, generating fallback data.")
                data_results[name] = generate_fallback_data(name)
        except Exception as e:
            print(f"Error fetching data for {name}: {e}")
            data_results[name] = generate_fallback_data(name)
            
    return data_results

def generate_fallback_data(name):
    """Generates synthetic 1-month data if yfinance fails."""
    import numpy as np
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    base_price = {
        'BTCUSD': 65000,
        'GOLD': 2100,
        'SPX500': 5000,
        'NIFTY': 22000
    }.get(name, 100)
    
    # Generate a random walk
    prices = base_price + np.cumsum(np.random.randn(30) * (base_price * 0.02))
    df = pd.DataFrame({'Close': prices}, index=dates)
    return df
