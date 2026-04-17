#!/usr/bin/env bash
# Railway web process when the service root directory is `helpme_hub`.
set -euo pipefail

cd "$(dirname "$0")"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-helpme_hub.settings}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn helpme_hub.wsgi:application --bind "0.0.0.0:${PORT:-8000}"
