#!/bin/sh

sleep 10

python manage.py migrate
python manage.py createcachetable
python manage.py collectstatic  --noinput
python manage.py loaddata db.json

exec "$@"