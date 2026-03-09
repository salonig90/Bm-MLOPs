import os
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
from django.conf import settings
from django.shortcuts import render
from .models import ABTestRun

def ab_testing_index(request):
    """
    Displays current A/B tests between Linear Regression and ARIMA models.
    """
    # Configure MLflow
    # Use the running server to avoid Model Registry unsupported URI errors on Windows
    mlflow.set_tracking_uri("http://127.0.0.1:5001")
    client = MlflowClient()

    experiments = {
        "LR": "BTCUSD_Linear_Regression",
        "ARIMA": "BTCUSD_ARIMA_Forecasting"
    }

    lr_mse = None
    arima_mse = None

    # Fetch latest MSE for both models
    for model_key, exp_name in experiments.items():
        exp = client.get_experiment_by_name(exp_name)
        if exp:
            runs = client.search_runs(
                experiment_ids=[exp.experiment_id],
                order_by=["attributes.start_time DESC"],
                max_results=1
            )
            if runs:
                mse = runs[0].data.metrics.get('mse')
                if model_key == "LR":
                    lr_mse = mse
                else:
                    arima_mse = mse

    # Calculate Improvement (Lower MSE is better)
    improvement = 0.0
    winner = "N/A"
    if lr_mse is not None and arima_mse is not None and lr_mse > 0:
        improvement = ((lr_mse - arima_mse) / lr_mse) * 100
        winner = "ARIMA" if arima_mse < lr_mse else "Linear Regression"

    # For display in the table
    active_tests = [{
        'test_name': "Linear Regression vs ARIMA (Current)",
        'control_v': "LR Baseline",
        'treatment_v': "ARIMA Forecast",
        'improvement': f"{improvement:+.1f}%",
        'improvement_class': "success" if improvement > 0 else "danger",
        'status': "Active",
        'started_at': pd.Timestamp.now().strftime('%Y-%m-%d'),
        'winner': winner
    }]

    context = {
        'active_tests': active_tests,
        'past_tests': [], # Simplified for now
        'lr_mse': f"{lr_mse:.4f}" if lr_mse else "N/A",
        'arima_mse': f"{arima_mse:.4f}" if arima_mse else "N/A",
        'improvement': f"{improvement:.1f}%",
        'winner': winner
    }
    return render(request, 'dashboard/ab_testing_index.html', context)
