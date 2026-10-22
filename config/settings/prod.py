"""
Production settings for Isezerano project.

Optimized for high performance, security, and caching.
"""
from .base import *  # noqa: F401, F403
from .base import env_var

DEBUG = False

# Enforce secure HTTPS redirection & cookies
SECURE_SSL_REDIRECT = env_var('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = int(env_var('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Redis Cache configuration
REDIS_URL = env_var('REDIS_URL', 'redis://127.0.0.1:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'KEY_PREFIX': 'isezerano_cache',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Production static files compression & caching
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}
