import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import train_test_split
import mlflow
import importlib
import os
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MLRUNS_DIR = os.path.join(PROJECT_ROOT, "ml", "mlruns")
os.environ["MLFLOW_TRACKING_URI"] = f"file:{MLRUNS_DIR}"

mlflow.set_experiment("BTCUSD_Linear_Regression")

def train_linear_regression(test_size=0.2):
    """
    Trains a Linear Regression model to predict the next period Close price.
    Uses 'Close', 'MA7', 'MA21', 'Daily_Return', 'Volume', 'STD7', 'SMMA7' as features.
    """
    data_path = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "btcusd_processed.csv")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run ingestion.py first.")
        return

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    
    # Feature Engineering for Linear Regression
    df['Target'] = df['Close'].shift(-1)
    df = df.dropna()
    
    # Updated features to include RSI
    features = ['Close', 'MA7', 'MA21', 'Daily_Return', 'Volume', 'STD7', 'SMMA7', 'RSI']
    X = df[features]
    y = df['Target']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
    
    mlflow.set_experiment("BTCUSD_Linear_Regression")
    with mlflow.start_run(run_name="Linear_Regression_Baseline"):
        # Log parameters
        mlflow.log_param("model_type", "LinearRegression")
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("features", features)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict test set
        predictions = model.predict(X_test)
        
        # Next Hour Prediction
        last_features = X.iloc[-1].values.reshape(1, -1)
        pred_next = model.predict(last_features)[0]
        
        # Metrics
        mse = mean_squared_error(y_test, predictions)
        mae = mean_absolute_error(y_test, predictions)
        
        # Log metrics
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("last_close_price", float(X.iloc[-1]['Close']))
        mlflow.log_metric("predicted_next_hour_close", float(pred_next))
        
        # Log model with registry
        mlflow_sklearn = importlib.import_module("mlflow.sklearn")
        model_info = mlflow_sklearn.log_model(
            model, 
            "model",
            registered_model_name="BTCUSD_Linear_Regression"
        )
        
        print(f"Linear Regression Training complete.")
        print(f"MSE: {mse:.4f}, MAE: {mae:.4f}")
        print(f"Predicted Next Hour Close: {pred_next:.4f}")
        print(f"Model registered as 'BTCUSD_Linear_Regression' at: {model_info.model_uri}")
        
        return model, mse, mae, pred_next

def predict_next_hour():
    """
    Fits Linear Regression on all available (X_t -> Close_{t+1}) and predicts Close_{t+1}
    from the most recent feature row (hourly data implies next hour).
    """
    data_path = os.path.join(PROJECT_ROOT, "ml", "data", "processed", "btcusd_processed.csv")
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run ingestion.py first.")
        return

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    # Updated features to include RSI
    features = ['Close', 'MA7', 'MA21', 'Daily_Return', 'Volume', 'STD7', 'SMMA7', 'RSI']
    df = df.ffill()
    df['Target'] = df['Close'].shift(-1)
    df_train = df.dropna()
    if len(df_train) < 10:
        print("Not enough data to train for next-hour prediction.")
        return

    X_all = df_train[features]
    y_all = df_train['Target']
    model = LinearRegression()
    model.fit(X_all, y_all)

    last_features = df[features].iloc[-1].values.reshape(1, -1)
    pred_next = model.predict(last_features)[0]
    last_ts = pd.to_datetime(df.index[-1])
    next_ts = last_ts + pd.Timedelta(hours=1)

    with mlflow.start_run(run_name="Linear_Regression_NextHour_Inference"):
        mlflow.log_param("model_type", "LinearRegression")
        mlflow.log_param("inference", True)
        mlflow.log_metric("predicted_next_hour_close", float(pred_next))

    print(f"Last timestamp: {last_ts}")
    print(f"Predicted Close at {next_ts}: {pred_next:.4f}")
    return pred_next, next_ts

if __name__ == "__main__":
    try:
        predict_next_hour()
    except Exception as e:
        print(f"Training failed: {e}")
