import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()
from articles.views import CategoryListView
print('CategoryListView imported successfully:', CategoryListView)