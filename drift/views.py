import os
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot
from django.shortcuts import render
from django.conf import settings
from datetime import datetime, timedelta

def drift_monitoring(request):
    """
    Drift Monitoring View - Analyzes price distributions and error trends.
    Simple drift detection logic: Compare recent 24h data with the baseline (last 40 days).
    """
    data_path = os.path.join(settings.BASE_DIR, "ml", "data", "processed", "btcusd_processed.csv")
    
    drift_status = "Unknown"
    drift_detected = False
    drift_magnitude = 0
    drift_details = []
    plot_div = ""
    last_updated = ""

    if os.path.exists(data_path):
        try:
            # Load Data
            df = pd.read_csv(data_path, index_col=0, parse_dates=True)
            if not df.empty and len(df) > 48:
                # Baseline: whole window (or e.g. last 40 days if available)
                baseline_mean = df["Close"].mean()
                
                # Recent: last 24h
                recent_df = df.tail(24)
                recent_mean = recent_df["Close"].mean()
                
                drift_magnitude = abs(recent_mean - baseline_mean) / baseline_mean if baseline_mean != 0 else 0
                drift_detected = drift_magnitude > 0.05  # 5% shift as threshold
                
                last_updated = df.index[-1].strftime('%Y-%m-%d %H:%M')
                
                # Analyze Drift for key features for the details table
                features_to_check = ['Close', 'RSI', 'Volume']
                for feat in features_to_check:
                    if feat in df.columns:
                        ref_mean = df[feat].mean()
                        curr_mean = df.tail(24)[feat].mean()
                        mean_diff = curr_mean - ref_mean
                        pct_change = (mean_diff / ref_mean) * 100 if ref_mean != 0 else 0
                        
                        threshold = 5 if feat == 'Close' else 15
                        status = "Warning" if abs(pct_change) > threshold else "OK"
                            
                        drift_details.append({
                            'feature': feat,
                            'recent_mean': f"{curr_mean:,.2f}",
                            'prev_mean': f"{ref_mean:,.2f}",
                            'change': f"{pct_change:+.2f}%",
                            'status': status
                        })
                
                drift_status = "Drift Detected" if drift_detected else "Stable"
                
                # Build chart - Histogram for distribution comparison
                fig = go.Figure()
                
                # Reference Distribution (Historical)
                fig.add_trace(go.Histogram(
                    x=df["Close"],
                    name='Baseline (Historical)',
                    histnorm='probability density',
                    marker_color='rgba(100, 100, 100, 0.5)',
                    nbinsx=50
                ))
                
                # Current Distribution (Recent 24h)
                fig.add_trace(go.Histogram(
                    x=recent_df["Close"],
                    name='Recent (Last 24h)',
                    histnorm='probability density',
                    marker_color='rgba(247, 147, 26, 0.7)',
                    nbinsx=30
                ))
                
                fig.update_layout( 
                    title="BTCUSD Price Distribution Shift", 
                    xaxis_title="Price (USD)", 
                    yaxis_title="Probability Density", 
                    barmode='overlay',
                    height=500, 
                    template="plotly_white",
                    font=dict(color='#333'),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                
                plot_div = plot(fig, output_type='div', include_plotlyjs=True)
                
                # Volume shift calculation
                try:
                    if df["Daily_Return"].std() != 0:
                        vol_shift = (df["Daily_Return"].tail(168).std() / df["Daily_Return"].std() - 1) * 100
                    else:
                        vol_shift = 0
                except Exception:
                    vol_shift = 0
            else:
                drift_status = "Insufficient Data"
                vol_shift = 0
        except Exception as e:
            print(f"Error in drift analysis: {e}")
            drift_status = "Error"
            vol_shift = 0
    else:
        vol_shift = 0

    context = {
        "drift_status": drift_status,
        "drift_detected": drift_detected,
        "drift_magnitude": drift_magnitude,
        "drift_details": drift_details,
        "plot_div": plot_div,
        "current_ma7": df["MA7"].iloc[-1] if "MA7" in df.columns else 0, 
        "baseline_ma7": df["MA7"].mean() if "MA7" in df.columns else 0, 
        "vol_shift": vol_shift,
        "last_updated": last_updated
    }
    
    return render(request, 'drift/drift.html', context)
