#!/usr/bin/env bash
set -e

python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; u,_=User.objects.get_or_create(username='root', defaults={'email':'root@example.com','is_staff':True,'is_superuser':True}); u.is_staff=True; u.is_superuser=True; u.set_password('rootpass123'); u.save()"
