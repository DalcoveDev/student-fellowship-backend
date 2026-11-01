"""
Development settings for Isezerano project.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# In dev, allow localhost and any local addresses if not explicitly set
ALLOWED_HOSTS = ['*']

# CORS / CSRF lax in development
CORS_ALLOW_ALL_ORIGINS = True

# Dummy or local memory cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Keep cookies non-secure over HTTP in local development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
