import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review_radar.settings')

app = Celery('review_radar')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()