#!/bin/sh
set -eu
python manage.py check --deploy --fail-level WARNING
python manage.py migrate --noinput
python manage.py configurer_roles
python manage.py collectstatic --noinput
exec waitress-serve --listen=0.0.0.0:8000 --trusted-proxy='*' --trusted-proxy-headers=x-forwarded-proto config.wsgi:application
