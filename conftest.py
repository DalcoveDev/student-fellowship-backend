import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-ci')
os.environ.setdefault('DEBUG', 'True')
