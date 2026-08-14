from celery import shared_task
from django.utils import timezone

@shared_task
def publish_scheduled_articles():
    # Move model import inside task to prevent premature app loading issues
    from .models import Article
    
    now = timezone.now()
    # Find scheduled articles whose release time has arrived
    scheduled_articles = Article.objects.filter(
        status='scheduled',
        published_at__lte=now
    )
    
    count = scheduled_articles.update(status='published')
    return f"Successfully published {count} scheduled articles at {now}"
