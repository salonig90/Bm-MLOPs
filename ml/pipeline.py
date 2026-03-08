import os
import sys
import argparse

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if CURR_DIR not in sys.path:
    sys.path.insert(0, CURR_DIR)

from data.ingestion import download_btcusd_data, preprocess_data
from models.linear_regression import train_linear_regression
from models.arima_model import train_arima_model


def run_pipeline(skip_ingestion=False, models=("lr", "arima"), period="730d", interval="1h"):
    if not skip_ingestion:
        df = download_btcusd_data(period=period, interval=interval)
        preprocess_data(df)

    results = {}
    if "lr" in models:
        lr_out = train_linear_regression()
        if lr_out:
            model, mse, mae, pred_next = lr_out
            results["linear_regression"] = {"mse": mse, "mae": mae, "prediction": pred_next}
            print(f"[LinearRegression] mse={mse:.4f}, mae={mae:.4f}, pred={pred_next:.4f}")

    if "arima" in models:
        arima_out = train_arima_model()
        if arima_out:
            model_fit, mse, pred_next = arima_out
            results["arima"] = {"mse": mse, "prediction": pred_next}
            print(f"[ARIMA] mse={mse:.4f}, pred={pred_next:.4f}")

    return results


def parse_args():
    p = argparse.ArgumentParser(description="End-to-end pipeline: ingestion + models")
    p.add_argument("--skip-ingestion", action="store_true", help="Skip data download/preprocess")
    p.add_argument("--models", type=str, default="lr,arima", help="Comma-separated: lr, arima")
    p.add_argument("--period", type=str, default="730d", help="Yahoo period for download")
    p.add_argument("--interval", type=str, default="1h", help="Yahoo interval for download")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    models = tuple(m.strip() for m in args.models.split(",") if m.strip())
    run_pipeline(skip_ingestion=args.skip_ingestion, models=models, period=args.period, interval=args.interval)
