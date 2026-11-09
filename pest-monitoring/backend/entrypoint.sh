#!/bin/sh
# Container start-up for Azure App Service (Part 3, Task 2).
# Runs on every start, so a fresh container always has an up-to-date schema and reference data.
set -e

python manage.py migrate --noinput
python manage.py seed_reference_data

# Optional demo admin account: set DJANGO_SUPERUSER_USERNAME/_EMAIL/_PASSWORD as app settings.
# "|| true" because the account already exists after the first start.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput || true
fi

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 120 \
    --access-logfile -