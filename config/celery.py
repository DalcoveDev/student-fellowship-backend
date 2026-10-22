import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

app = Celery('isezerano')

# Configure Celery using values from Django settings (namespace CELERY_*)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in registered Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
