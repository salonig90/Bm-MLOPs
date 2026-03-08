import yfinance as yf
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas_ta as ta

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

def download_btcusd_data(symbol="BTCUSD", exchange="BINANCE", interval="1h", n_bars=2000, period=None):
    """
    Downloads historical BTCUSD data from TradingView using tvdatafeed.
    Falls back to Yahoo Finance if tvdatafeed fails.
    """
    print(f"Downloading data for {symbol} from {exchange} via tvdatafeed...")
    try:
        from tvDatafeed import TvDatafeed, Interval
        tv = TvDatafeed()
        # Map interval string to Interval enum
        interval_map = {
            "1h": Interval.in_1_hour,
            "1d": Interval.in_daily,
            "1m": Interval.in_1_minute,
            "5m": Interval.in_5_minute,
            "15m": Interval.in_15_minute
        }
        tv_interval = interval_map.get(interval, Interval.in_1_hour)
        
        data = tv.get_hist(symbol=symbol, exchange=exchange, interval=tv_interval, n_bars=n_bars)
        
        if data is None or data.empty:
            print("tvdatafeed returned empty data. Falling back to Yahoo Finance...")
            return download_btcusd_data_yfinance(period=period if period else "730d", interval=interval)
            
        # Clean up columns (tvdatafeed returns lowercase by default usually, but let's be safe)
        data.columns = [col.capitalize() for col in data.columns]
        
        os.makedirs(str(RAW_DIR), exist_ok=True)
        file_path = RAW_DIR / f"{symbol.lower()}_historical.csv"
        data.to_csv(str(file_path))
        print(f"Data saved to {file_path}")
        return data
        
    except Exception as e:
        print(f"Error with tvdatafeed: {e}. Falling back to Yahoo Finance...")
        return download_btcusd_data_yfinance(period=period if period else "730d", interval=interval)

def download_btcusd_data_yfinance(symbol="BTC-USD", period="730d", interval="1h"):
    """
    Fallback: Downloads historical BTC-USD data from Yahoo Finance.
    """
    print(f"Downloading fallback data from Yahoo Finance for {symbol}...")
    try:
        data = yf.download(symbol, period=period, interval=interval)
        if data is None or data.empty:
            raise ValueError("Yahoo Finance data is empty.")
            
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        os.makedirs(str(RAW_DIR), exist_ok=True)
        file_path = RAW_DIR / f"{symbol.lower().replace('-', '')}_historical.csv"
        data.to_csv(str(file_path))
        return data
    except Exception as e:
        print(f"Error downloading fallback data: {e}")
        return None

def preprocess_data(df):
    """
    Enhanced preprocessing using pandas_ta for robust technical indicators.
    """
    if df is None or df.empty:
        return None
    
    # Ensure column names are correct for pandas_ta
    df.columns = [col.capitalize() for col in df.columns]
    
    # Fill missing values
    df = df.ffill().bfill()
    
    # Use pandas_ta for more reliable indicators
    # Moving Averages
    df['MA7'] = ta.sma(df['Close'], length=7)
    df['MA21'] = ta.sma(df['Close'], length=21)
    
    # Returns
    df['Daily_Return'] = ta.percent_return(df['Close'])
    
    # Volatility (STD)
    df['STD7'] = df['Close'].rolling(window=7).std()
    
    # SMMA (using pandas_ta rma which is equivalent to SMMA)
    df['SMMA7'] = ta.rma(df['Close'], length=7)
    
    # RSI (Extra feature for better prediction)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Drop rows with NaN from rolling calculations
    df = df.dropna()
    
    os.makedirs(str(PROCESSED_DIR), exist_ok=True)
    processed_path = PROCESSED_DIR / "btcusd_processed.csv"
    df.to_csv(str(processed_path))
    print(f"Processed data saved to {processed_path}")
    return df

if __name__ == "__main__":
    raw_data = download_btcusd_data()
    if raw_data is not None:
        processed_data = preprocess_data(raw_data)
        print("Data Ingestion and Preprocessing Complete.")
