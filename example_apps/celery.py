import os

from celery import Celery, schedules

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_cache.tests.settings")

app = Celery()
app.config_from_object("django.conf:settings")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
app.conf.timezone = "UTC"
app.conf.broker_url = "redis://localhost:6379/0"
