#!/bin/sh
set -eu

# Prepare the database and CSS before starting the website.
python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0

# Two workers allow an approval request to call our own signed endpoint.
exec gunicorn news_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 \
    --access-logfile - --error-logfile -
