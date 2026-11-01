import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('pulse_backend')

# Configure Celery using values from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Broker / Backend Redis settings
app.conf.broker_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
app.conf.result_backend = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

# Auto-discover tasks in registered Django apps
app.autodiscover_tasks()

# Periodically promote scheduled articles whose publication time has arrived.
# The public API also does this on read, so scheduling still works if Celery
# beat/worker is unavailable.
app.conf.beat_schedule = {
    'publish-scheduled-articles-every-minute': {
        'task': 'articles.tasks.publish_scheduled_articles',
        'schedule': 60.0,
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
