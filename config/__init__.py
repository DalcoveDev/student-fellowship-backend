# Defer celery import to prevent premature Django app loading issues.
# The Celery worker will load the configuration directly via the -A flag:
#   celery -A config worker -l info
#
# If you need to make Celery active in Django process context, uncomment:
# from .celery import app as celery_app
# __all__ = ('celery_app',)
