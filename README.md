# VORTEX ALPHA | Neural Market Intelligence

VORTEX ALPHA is a professional-grade quantitative forecasting platform for Bitcoin and global financial assets. It utilizes advanced neural architectures, specifically ARIMA and Linear Regression, to decode market dynamics and provide high-fidelity predictive signals.

## 🚀 Features

- **Neural Forecasting**: Hourly and daily price predictions for BTCUSD.
- **Multi-Asset Intelligence**: Real-time tracking and 1-month historical analysis for BTC, GOLD, SPX500, and NIFTY.
- **Drift Monitoring**: Automated detection of model performance degradation and feature distribution shifts.
- **ROI Analytics**: Simulated trading strategy performance and risk reduction metrics.
- **A/B Testing**: Side-by-side comparison of different model architectures (e.g., LR vs ARIMA).
- **Interactive Visualizations**: High-performance Plotly charts for deep market analysis.

## 🛠️ Technology Stack

- **Backend**: Django (Python)
- **ML Operations**: MLflow (Tracking & Model Registry)
- **Data Science**: Pandas, Scikit-learn, Statsmodels (ARIMA)
- **Visualizations**: Plotly.js
- **Frontend**: Bootstrap 5, Space Grotesk Typography

## 📋 Prerequisites

Ensure you have the following installed:
- Python 3.9+
- Pip (Python Package Manager)

## 🏃 Setup & Installation

Follow these steps to run the project locally:

### 1. Clone & Install Dependencies
```bash
# Install required libraries
pip install -r requirements.txt
```

### 2. Initialize the Database
```bash
# Setup the SQLite database and models
python manage.py makemigrations
python manage.py migrate
```

### 3. Start the MLflow Server
To track and view your experiments, open a **new terminal window** and start the MLflow server:
```bash
python -m mlflow server --port 5001 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns
```
*Note: Keep this terminal running. You can view all experiments, including `BTC-USD_Arima_Saloni` and `BTC-USD_LR_Saloni`, at [http://127.0.0.1:5001/](http://127.0.0.1:5001/).*

### 4. Run the Web Server
In your main terminal, launch the Django application:
```bash
python manage.py runserver 8500
```

### 5. Access the Platform
- **Landing Page**: [http://127.0.0.1:8500/](http://127.0.0.1:8500/)
- **Forecasting Dashboard**: [http://127.0.0.1:8500/dashboard/](http://127.0.0.1:8500/dashboard/)
- **MLflow Experiment UI**: [http://127.0.0.1:5001/](http://127.0.0.1:5001/)

## 🧪 Viewing MLflow Experiments

To view specific experiment details, model versions, and performance metrics (MSE, MAE, Predicted Prices):
1. Ensure the MLflow server is running (Step 3).
2. Open [http://127.0.0.1:5001/](http://127.0.0.1:5001/) in your browser.
3. Select your experiment from the left sidebar (e.g., `BTC-USD_LR_Saloni`).
4. Click on individual runs to see detailed logs and charts.

## 📊 Project Structure

- `/homepage`: Market intelligence landing page logic.
- `/dashboard`: Core forecasting overview and pipeline controls.
- `/drift`: Model performance and data drift analysis.
- `/roi`: Financial impact and simulated profitability metrics.
- `/ab_testing`: Model version comparison dashboard.
- `/ml`: Machine learning models and processing pipelines.

---
&copy; 2026 VORTEX ALPHA. Neural Market Intelligence.
