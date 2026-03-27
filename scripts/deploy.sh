#!/bin/bash
set -e
cd ~/leatherwork-in-traveling-db
git pull
source ~/.virtualenvs/leatherwork/bin/activate
pip install -r requirements/base.txt
python manage.py migrate
python manage.py collectstatic --noinput