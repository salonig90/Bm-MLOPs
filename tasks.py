import subprocess
import os
import logging
from celery import shared_task
from celery.utils.log import get_task_logger

# Setup logging
logger = get_task_logger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PIPELINE_SCRIPT = os.path.join(PROJECT_ROOT, "ml", "pipeline.py")

@shared_task(name="tasks.run_ml_pipeline")
def run_ml_pipeline():
    """
    Celery task that executes the ML pipeline script.
    """
    logger.info("Starting Celery-scheduled ML pipeline run...")
    try:
        # Using the same command as the 'Run Pipeline' button in the dashboard
        result = subprocess.run(
            ["python3", PIPELINE_SCRIPT, "--models", "lr,arima"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Pipeline executed successfully via Celery.")
        return f"Pipeline Output: {result.stdout[:200]}..."
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline execution failed with error: {e}")
        logger.error(f"Error Output: {e.stderr}")
        raise e
    except Exception as e:
        logger.error(f"An unexpected error occurred in Celery task: {e}")
        raise e
