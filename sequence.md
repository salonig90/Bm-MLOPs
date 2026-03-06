# Sequence Diagram: End-to-End Flow

This file documents how the project components trigger and interact end-to-end:
- Data ingestion produces CSVs used by training and monitoring.
- Model training logs runs and (optionally) registers models in MLflow.
- MLflow server exposes the UI for experiments and registry.
- Django dashboard reads experiment + registry metadata from MLflow.
- Drift detection compares reference vs current datasets and produces an HTML report.
- A/B testing and ROI modules use stored metrics (and model versions) to compare outcomes.

## How MLflow “Starts” the System (It Doesn’t)

MLflow does not orchestrate or trigger ingestion/training/dashboard by itself.

In this repo, MLflow is used in a passive way:
- Training scripts call MLflow APIs (`mlflow.start_run`, `mlflow.log_metric`, `mlflow.log_model`) while they run.
- Those APIs write metadata + artifacts into the tracking backend (currently the local filesystem at `./mlruns`).
- The MLflow server is only a UI/API layer that reads from the same tracking backend so you can view runs in the browser.
- Django uses `MlflowClient()` to read run/registry metadata at request-time. Depending on configuration, it can read from the local store or from a remote tracking server.

Two common modes:
- Local-only (no MLflow server): scripts still log to `./mlruns`; you just don’t have the web UI.
- With MLflow server: you start the server process; the UI becomes available and reads the same `./mlruns` store.

## Main Flow (Ingestion → Training → MLflow → Dashboard)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Ingestion as src/data/ingestion.py
  participant Raw as data/raw/*.csv
  participant Processed as data/processed/btcusd_processed.csv
  participant LR as src/models/linear_regression.py
  participant ARIMA as src/models/arima_model.py
  participant MLflowTracking as MLflow Tracking Store (./mlruns)
  participant MLflowUI as MLflow Server (python -m mlflow server)
  participant Django as Django Dashboard (dashboard/)
  participant MlflowClient as MLflow Client (Django)

  User->>Ingestion: Run ingestion script
  Ingestion->>Raw: Write raw BTCUSD history CSV
  Ingestion->>Processed: Write processed features CSV

  alt Train Linear Regression
    User->>LR: Run training script
    LR->>Processed: Read processed CSV (features + target)
    LR->>MLflowTracking: Log params + metrics + artifacts
    LR->>MLflowTracking: Register model (BTCUSD_Linear_Regression)
  end

  alt Train ARIMA
    User->>ARIMA: Run training script
    ARIMA->>Processed: Read processed CSV (Close series)
    ARIMA->>MLflowTracking: Log params + metrics
  end

  Note over LR,ARIMA: Logging happens even if MLflow server is not running

  User->>MLflowUI: Start MLflow server
  MLflowUI->>MLflowTracking: Read experiments + runs + registry
  User->>MLflowUI: Open MLflow UI in browser

  User->>Django: Start Django server
  User->>Django: Open dashboard pages in browser
  Django->>MlflowClient: Query runs for experiment(s)
  MlflowClient->>MLflowTracking: Fetch runs + metrics
  Django->>MlflowClient: Query registered model versions
  MlflowClient->>MLflowTracking: Fetch registry metadata
  Django-->>User: Render dashboard (runs, metrics, versions)
```

## MLflow Server Access Pattern (UI)

This is the part that often causes confusion: the MLflow server does not “start training”; it only serves the UI/API.

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Browser as Browser
  participant MLflowUI as MLflow Server (python -m mlflow server)
  participant MLflowTracking as Tracking Store (./mlruns)

  User->>MLflowUI: Start MLflow server process
  Browser->>MLflowUI: GET /
  MLflowUI->>MLflowTracking: Read experiments/runs/models
  MLflowUI-->>Browser: Render MLflow UI
```

## When You See HTTP 403 on MLflow UI

Some environments block `localhost` access due to MLflow’s security middleware defaults.
If needed, start MLflow with explicit host/CORS/allowed-hosts for development:

```bash
python3 -m mlflow server --host 0.0.0.0 --port 5001 --backend-store-uri ./mlruns --allowed-hosts "*" --cors-allowed-origins "*"
```

## Monitoring Flow (Drift Detection)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Ingestion as src/data/ingestion.py
  participant Processed as data/processed/btcusd_processed.csv
  participant Drift as src/monitoring/drift_detection.py
  participant Reports as reports/drift/*.html
  participant Django as Django Dashboard (dashboard/)

  User->>Ingestion: Run ingestion script (current data)
  Ingestion->>Processed: Update processed CSV

  User->>Drift: Run drift check
  Drift->>Processed: Load reference dataset (train snapshot)
  Drift->>Processed: Load current dataset
  Drift->>Reports: Write drift report HTML
  Drift-->>User: Print drift status (dataset drift true/false)

  opt Display in dashboard
    User->>Django: Open monitoring page
    Django-->>User: Link/embed latest drift report (HTML)
  end
```

## A/B Testing & ROI Flow (High-Level)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Django as Django Dashboard (dashboard/)
  participant AB as dashboard/ab_testing (DB models)
  participant ROI as dashboard/roi (DB models)
  participant MlflowClient as MLflow Client (Django)
  participant MLflowTracking as MLflow Tracking Store (./mlruns)

  User->>Django: Start an A/B test (select control + treatment versions)
  Django->>MlflowClient: Fetch metrics for both versions/runs
  MlflowClient->>MLflowTracking: Read metrics + params
  Django->>AB: Persist A/B test record (versions + result)
  AB-->>Django: Stored A/B test result

  User->>Django: View ROI page
  Django->>ROI: Read ROI metrics (simulated/recorded)
  ROI-->>Django: ROI time series + summary
  Django-->>User: Render ROI + A/B summaries
```

## Trigger Summary

- Ingestion is user-triggered by running [ingestion.py](file:///Users/amolc/2026/timeseries/src/data/ingestion.py), producing raw + processed CSV outputs.
- Training is user-triggered by running:
  - [linear_regression.py](file:///Users/amolc/2026/timeseries/src/models/linear_regression.py)
  - [arima_model.py](file:///Users/amolc/2026/timeseries/src/models/arima_model.py)
- MLflow UI is user-triggered by starting the MLflow server (the UI reads from the tracking store; it does not trigger training).
- Django UI is user-triggered by starting the Django server; it reads MLflow metadata at request time via `MlflowClient` (local store or remote tracking server, depending on configuration).
- Drift detection is user-triggered by running [drift_detection.py](file:///Users/amolc/2026/timeseries/src/monitoring/drift_detection.py), which writes an HTML report.
