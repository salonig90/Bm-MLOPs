import os
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
from django.shortcuts import render
import plotly.graph_objects as go
from plotly.offline import plot
from .utils import get_landing_assets_data

# Configure MLflow
MLFLOW_TRACKING_URI = "http://127.0.0.1:5001"

def landing_page(request):
    """
    Enhanced landing page with 3-month interactive data for BTC, GOLD, SPX500, and NIFTY.
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    latest_prediction_lr = "N/A"
    
    # Get LR Prediction for BTC
    try:
        exp = client.get_experiment_by_name("BTC-USD_LR_Saloni")
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
                hovermode=False,
                autosize=True
            )
            mini_plot = plot(fig_mini, output_type='div', include_plotlyjs=False, show_link=False, config={'displayModeBar': False, 'responsive': True})
            
            # Main interactive graph for the modal/module
            fig_main = go.Figure()
            fig_main.add_trace(go.Scatter(
                x=df.index, 
                y=df['Close'], 
                mode='lines', 
                name=f'{name} Price',
                line=dict(color='#8b5cf6', width=3),
                fill='tozeroy',
                fillcolor='rgba(139, 92, 246, 0.1)',
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
                    line=dict(color='#8b5cf6', width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                fig_main.add_trace(go.Scatter(
                    x=[next_time], 
                    y=[float(latest_prediction_lr)], 
                    mode='markers',
                    name='LR Prediction',
                    marker=dict(size=12, symbol='star', color='#c084fc', line=dict(color='white', width=1)),
                    hovertemplate='<b>LR Forecast:</b> $%{y:,.2f}<br><b>Date:</b> %{x}<extra></extra>'
                ))

            fig_main.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Space Grotesk'),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(139, 92, 246, 0.1)', 
                    zeroline=False,
                    tickfont=dict(color='#94a3b8')
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(139, 92, 246, 0.1)', 
                    zeroline=False,
                    tickfont=dict(color='#94a3b8'),
                    tickprefix='$'
                ),
                margin=dict(l=40, r=20, t=40, b=40),
                height=450,
                showlegend=False,
                autosize=True,
                hoverlabel=dict(bgcolor='#0a0118', font_size=14, font_family='Space Grotesk')
            )
            main_plot = plot(fig_main, output_type='div', include_plotlyjs=True, config={'responsive': True})
            
            asset_info.append({
                'name': name,
                'price': f"{latest_price:,.2f}",
                'change': f"{price_change:+,.2f}",
                'pct_change': f"{pct_change:+.2f}%",
                'is_positive': pct_change >= 0,
                'mini_plot': mini_plot,
                'main_plot': main_plot
            })
            
    return render(request, 'homepage/landing.html', {'asset_info': asset_info, 'latest_prediction_lr': latest_prediction_lr})
