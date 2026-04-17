#!/usr/bin/env bash
# Railway web process: migrate, collect static assets, then gunicorn.
# Run from repository root (see root Procfile / railway.json).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/helpme_hub"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-helpme_hub.settings}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn helpme_hub.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
