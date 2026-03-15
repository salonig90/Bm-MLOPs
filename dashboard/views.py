import os
import subprocess
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
from django.shortcuts import render, redirect
from django.conf import settings
import plotly.graph_objects as go
from plotly.offline import plot

# Configure MLflow
MLFLOW_TRACKING_URI = "http://127.0.0.1:5001"

def dashboard_overview(request):
    """
    Fetches experiment data and model registry info from MLflow for the dashboard.
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    
    latest_prediction_lr = "N/A"
    latest_prediction_arima = "N/A"
    latest_price = "N/A"
    model_accuracy = "N/A"
    runs_data = []

    experiments = {
        "LR": "BTC-USD_LR_Saloni",
        "ARIMA": "BTC-USD_Arima_Saloni"
    }

    # Get Registered Model Info
    registered_models = ["BTC-USD_LR_Saloni", "BTC-USD_Arima_Saloni"]
    latest_versions = []
    for model_name in registered_models:
        try:
            rm = client.get_registered_model(model_name)
            versions = rm.latest_versions
            if versions:
                latest_versions.extend(versions)
        except Exception:
            continue

    for model_key, exp_name in experiments.items():
        try:
            exp = client.get_experiment_by_name(exp_name)
            if exp:
                runs = client.search_runs(
                    experiment_ids=[exp.experiment_id],
                    order_by=["attributes.start_time DESC"],
                    max_results=10
                )
                for run in runs:
                    m_type = run.data.params.get('model_type', model_key)
                    mse = run.data.metrics.get('mse', 'N/A')
                    pred = run.data.metrics.get('predicted_next_hour_close', 'N/A')
                    
                    if model_key == "LR" and latest_prediction_lr == "N/A" and pred != "N/A":
                        latest_prediction_lr = f"{pred:.2f}"
                    elif model_key == "ARIMA" and latest_prediction_arima == "N/A" and pred != "N/A":
                        latest_prediction_arima = f"{pred:.2f}"

                    runs_data.append({
                        'run_id': run.info.run_id,
                        'status': run.info.status,
                        'model_type': m_type,
                        'mse': mse,
                        'start_time': pd.to_datetime(run.info.start_time, unit='ms').strftime('%Y-%m-%d %H:%M')
                    })
        except Exception as e:
            print(f"Error fetching runs for {model_key}: {e}")

    runs_data = sorted(runs_data, key=lambda x: x['start_time'], reverse=True)

    plot_div = ""
    try:
        data_path = os.path.join(settings.BASE_DIR, "ml", "data", "processed", "btcusd_processed.csv")
        if os.path.exists(data_path):
            df = pd.read_csv(data_path, index_col=0, parse_dates=True)
            if not df.empty:
                latest_price = f"{df.iloc[-1]['Close']:.2f}"
                
                fig = go.Figure()
                df_recent = df.tail(48)
                fig.add_trace(go.Scatter(
                    x=df_recent.index, 
                    y=df_recent['Close'], 
                    mode='lines+markers', 
                    name='Actual Price',
                    line=dict(color='#f7931a', width=3),
                    marker=dict(size=6, color='#f7931a')
                ))
                
                last_time = df_recent.index[-1]
                next_time = last_time + pd.Timedelta(hours=1)
                
                if latest_prediction_lr != "N/A":
                    fig.add_trace(go.Scatter(x=[next_time], y=[float(latest_prediction_lr)], 
                                           mode='markers', name='LR Prediction', marker=dict(size=14, symbol='star', color='#00ff00')))
                if latest_prediction_arima != "N/A":
                    fig.add_trace(go.Scatter(x=[next_time], y=[float(latest_prediction_arima)], 
                                           mode='markers', name='ARIMA Prediction', marker=dict(size=12, symbol='diamond', color='#00bcff')))
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    title=dict(text="BTCUSD Price & Next Hour Forecast", font=dict(size=20)),
                    xaxis=dict(title="Timeline (Last 48 Hours)", gridcolor='#333', zerolinecolor='#333'),
                    yaxis=dict(title="Price (USD)", gridcolor='#333', zerolinecolor='#333'),
                    margin=dict(l=20, r=20, t=60, b=20),
                    height=500,
                    legend=dict(bgcolor='rgba(0,0,0,0.5)', bordercolor='#444')
                )
                plot_div = plot(fig, output_type='div', include_plotlyjs=True)
    except Exception as e:
        print(f"Error reading data or creating plot: {e}")

    valid_mse_runs = [r for r in runs_data if isinstance(r['mse'], (int, float))]
    if valid_mse_runs:
        best_run = min(valid_mse_runs, key=lambda x: x['mse'])
        model_accuracy = f"{best_run['mse']:.2f} (MSE - {best_run['model_type']})"

    context = {
        'latest_price': latest_price,
        'latest_prediction_lr': latest_prediction_lr,
        'latest_prediction_arima': latest_prediction_arima,
        'model_accuracy': model_accuracy,
        'runs': runs_data[:10],
        'latest_versions': latest_versions,
        'plot_div': plot_div
    }
    
    return render(request, 'dashboard/overview.html', context)

def run_pipeline_view(request):
    """
    Triggers the ML pipeline from the dashboard.
    """
    if request.method == "POST":
        try:
            pipeline_path = os.path.join(settings.BASE_DIR, "ml", "pipeline.py")
            subprocess.Popen(["python", pipeline_path, "--models", "lr,arima"])
        except Exception as e:
            print(f"Error triggering pipeline: {e}")
            
    return redirect('dashboard_overview')
