import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import mlflow
import os
import warnings

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Use the running server to avoid local URI issues and disconnected UI
mlflow.set_tracking_uri("http://127.0.0.1:5001")

mlflow.set_experiment("BTC-USD_Arima_Saloni")

# Suppress ARIMA warnings
warnings.filterwarnings("ignore")

def train_arima_model(p=5, d=1, q=0):
    """
    Trains an ARIMA model on BTCUSD Close price.
    p: Lag order
    d: Degree of differencing
    q: Order of moving average
    """
    data_path = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "btcusd_processed.csv")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run ingestion.py first.")
        return

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    # ARIMA uses univariate time series
    series = df['Close']
    
    # Split data (80% train, 20% test)
    split_point = int(len(series) * 0.8)
    train, test = series[0:split_point], series[split_point:]
    
    mlflow.set_experiment("BTC-USD_Arima_Saloni")
    with mlflow.start_run(run_name="ARIMA_Model"):
        # Log parameters
        mlflow.log_param("model_type", "ARIMA")
        mlflow.log_param("p", p)
        mlflow.log_param("d", d)
        mlflow.log_param("q", q)
        
        # Fit model
        print(f"Training ARIMA({p},{d},{q})...")
        model = ARIMA(train, order=(p, d, q))
        model_fit = model.fit()
        
        # Forecast test set
        forecast_result = model_fit.forecast(steps=len(test))
        predictions = forecast_result
        
        # Calculate MSE
        mse = mean_squared_error(test, predictions)
        
        # Next Hour Prediction
        # Re-fit on full data for best prediction? Or just use model_fit?
        # For the training run, model_fit is only trained on 80% data.
        # Let's perform a 1-step forecast on the FULL series for the final prediction
        full_model = ARIMA(series, order=(p, d, q))
        full_model_fit = full_model.fit()
        pred_next = float(full_model_fit.forecast(steps=1).iloc[0])
        
        # Log metrics
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("last_close_price", float(series.iloc[-1]))
        mlflow.log_metric("predicted_next_hour_close", pred_next)
        
        print(f"ARIMA Training complete.")
        print(f"MSE: {mse:.4f}")
        print(f"Predicted Next Hour Close: {pred_next:.4f}")
        
        return model_fit, mse, pred_next

def predict_next_hour(p=5, d=1, q=0, max_points=2000):
    """
    Fits ARIMA on the most recent hourly Close series and forecasts 1 step ahead.
    """
    data_path = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "btcusd_processed.csv")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run ingestion.py first.")
        return

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    if "Close" not in df.columns or df.empty:
        print("Processed data is missing 'Close' or is empty.")
        return

    series = df["Close"].dropna()
    if max_points is not None and len(series) > max_points:
        series = series.iloc[-max_points:]

    if len(series) < 50:
        print("Not enough data to fit ARIMA for next-hour prediction.")
        return

    last_ts = pd.to_datetime(series.index[-1])
    next_ts = last_ts + pd.Timedelta(hours=1)

    print(f"Fitting ARIMA({p},{d},{q}) on {len(series)} hourly points...")
    model = ARIMA(series, order=(p, d, q))
    model_fit = model.fit()
    pred_next = float(model_fit.forecast(steps=1).iloc[0])

    with mlflow.start_run(run_name="ARIMA_NextHour_Inference"):
        mlflow.log_param("model_type", "ARIMA")
        mlflow.log_param("inference", True)
        mlflow.log_param("p", p)
        mlflow.log_param("d", d)
        mlflow.log_param("q", q)
        mlflow.log_param("max_points", max_points)
        mlflow.log_metric("predicted_next_hour_close", pred_next)

    print(f"Last timestamp: {last_ts}")
    print(f"Predicted Close at {next_ts}: {pred_next:.4f}")
    return pred_next, next_ts

if __name__ == "__main__":
    try:
        predict_next_hour()
    except Exception as e:
        print(f"Training failed: {e}")
