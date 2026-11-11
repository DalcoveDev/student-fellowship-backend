"""
Settings package for the student fellowship backend.

Allows both:
1. Explicit submodule target:
   DJANGO_SETTINGS_MODULE=config.settings.dev
   DJANGO_SETTINGS_MODULE=config.settings.prod
2. Direct package target (backward compatibility):
   DJANGO_SETTINGS_MODULE=config.settings
"""
import os

_target = os.environ.get('DJANGO_SETTINGS_MODULE', '')
if _target in ('config.settings', 'config.settings.'):
    _env = os.environ.get('DJANGO_ENV', 'development').lower()
    if _env in ('prod', 'production') or os.environ.get('DEBUG', 'True').lower() == 'false':
        from .prod import *  # noqa: F401, F403
    else:
        from .dev import *  # noqa: F401, F403
