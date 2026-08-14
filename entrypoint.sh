#!/bin/sh
set -eu

echo "Waiting for PostgreSQL..."
python - <<'PY'
import os
import time

import psycopg2

deadline = time.time() + 60
while True:
    try:
        connection = psycopg2.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ.get("DB_HOST", "db"),
            port=os.environ.get("DB_PORT", "5432"),
        )
        connection.close()
        break
    except psycopg2.OperationalError:
        if time.time() >= deadline:
            raise
        time.sleep(2)
PY

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
