import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

from articles.views import (
    ArticleCommentListView,
    ArticleDetailView,
    ArticleListView,
    CategoryListView,
    CMSArticleViewSet,
    CMSCategoryViewSet,
    CMSCommentViewSet,
    CMSTagViewSet,
    CommentCreateView,
    TagListView,
)
print("All imports successful!")