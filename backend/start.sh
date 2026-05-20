#!/bin/sh
# Argus-Sentinel container entry point
# Routes to Celery worker or FastAPI based on SERVICE_TYPE env var

if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "[start.sh] Starting Celery worker..."
    exec celery -A tasks.celery_app worker --loglevel=info --concurrency=2
else
    echo "[start.sh] Running database migrations..."
    alembic upgrade head
    echo "[start.sh] Starting FastAPI server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
