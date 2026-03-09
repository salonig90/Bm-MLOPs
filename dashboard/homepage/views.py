import os
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
from django.shortcuts import render
from django.conf import settings
import plotly.graph_objects as go
from plotly.offline import plot
from .utils import get_landing_assets_data

def landing_page(request):
    """
    Enhanced landing page with 3-month interactive data for BTC, GOLD, SPX500, and NIFTY.
    """
    # Configure MLflow for BTC prediction
    # Use the running server to avoid Model Registry unsupported URI errors on Windows
    mlflow.set_tracking_uri("http://127.0.0.1:5001")
    
    client = MlflowClient()
    latest_prediction_lr = "N/A"
    
    # Get LR Prediction for BTC
    try:
        exp = client.get_experiment_by_name("BTCUSD_Linear_Regression")
        if exp:
            runs = client.search_runs(
                experiment_ids=[exp.experiment_id],
                order_by=["attributes.start_time DESC"],
                max_results=1
            )
            if runs:
                pred = runs[0].data.metrics.get('predicted_next_hour_close', 'N/A')
                if pred != "N/A":
                    latest_prediction_lr = f"{pred:.2f}"
    except Exception as e:
        print(f"Error fetching MLflow prediction: {e}")

    # Fetch 3-month data for all assets
    assets_data = get_landing_assets_data()
    
    asset_info = []
    
    for name, df in assets_data.items():
        if df is not None and not df.empty:
            # Latest price and change
            latest_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            price_change = latest_price - prev_price
            pct_change = (price_change / prev_price) * 100
            
            # Generate mini-graph for the card
            fig_mini = go.Figure()
            fig_mini.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                mode='lines',
                line=dict(color='#f7931a' if pct_change >= 0 else '#ff4d4d', width=2),
                fill='tozeroy',
                fillcolor='rgba(247, 147, 26, 0.1)' if pct_change >= 0 else 'rgba(255, 77, 77, 0.1)',
            ))
            fig_mini.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                margin=dict(l=0, r=0, t=0, b=0),
                height=60,
                showlegend=False,
                hovermode=False
            )
            mini_plot = plot(fig_mini, output_type='div', include_plotlyjs=False, show_link=False, config={'displayModeBar': False})
            
            # Main interactive graph for the modal/module
            fig_main = go.Figure()
            fig_main.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                mode='lines', 
                name=f'{name} Price',
                line=dict(color='#f7931a', width=2.5),
                fill='tozeroy',
                fillcolor='rgba(247, 147, 26, 0.05)',
                hovertemplate='<b>Price:</b> $%{y:,.2f}<br><b>Date:</b> %{x}<extra></extra>'
            ))
            
            # Add BTC forecast if this is the BTC asset
            if name == 'BTCUSD' and latest_prediction_lr != "N/A":
                last_time = df.index[-1]
                next_time = last_time + pd.Timedelta(days=1)
                fig_main.add_trace(go.Scatter(
                    x=[last_time, next_time],
                    y=[latest_price, float(latest_prediction_lr)],
                    mode='lines',
                    line=dict(color='#f7931a', width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                fig_main.add_trace(go.Scatter(
                    x=[next_time], 
                    y=[float(latest_prediction_lr)], 
                    mode='markers', 
                    name='AI Forecast', 
                    marker=dict(size=10, color='#00ff00', symbol='diamond'),
                    hovertemplate='<b>AI Forecast:</b> $%{y:,.2f}<extra></extra>'
                ))

            fig_main.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e0e0e0', family="Inter, sans-serif"),
                xaxis=dict(showgrid=False, showline=True, linecolor='#333', tickfont=dict(color='#666'), type='date'),
                yaxis=dict(showgrid=True, gridcolor='#1a1a1a', showline=False, tickfont=dict(color='#666'), side='right', tickformat='$,.2f'),
                margin=dict(l=0, r=0, t=10, b=0),
                height=400,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12, color='#888'), bgcolor='rgba(0,0,0,0)'),
                hovermode='x unified'
            )
            main_plot = plot(fig_main, output_type='div', include_plotlyjs=True if name == 'BTCUSD' else False)
            
            asset_info.append({
                'name': name,
                'price': f"{latest_price:,.2f}",
                'change': f"{price_change:,.2f}",
                'pct_change': f"{pct_change:+.2f}%",
                'is_positive': pct_change >= 0,
                'mini_plot': mini_plot,
                'main_plot': main_plot
            })

    return render(request, 'homepage/landing.html', {
        'asset_info': asset_info,
        'latest_prediction': latest_prediction_lr
    })

