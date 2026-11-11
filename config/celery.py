import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

app = Celery('student_fellowship')

# Configure Celery using values from Django settings (namespace CELERY_*)
app.config_from_object('django.conf:settings', namespace='CELERY')

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
