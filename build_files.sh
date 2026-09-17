#!/bin/bash
# Vercel build step: install dependencies and collect static files.
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
