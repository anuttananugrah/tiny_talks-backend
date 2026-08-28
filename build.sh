#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python tinytalks/manage.py collectstatic --no-input
python tinytalks/manage.py migrate
python manage.py createsuperuser --noinput --username admin --email tinytalksbysona@gmail.com || true