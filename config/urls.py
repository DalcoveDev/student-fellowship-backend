"""
URL configuration for the student fellowship site.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from announcements.views import (
    CMSAnnouncementViewSet,
    PublicAnnouncementDetailView,
    PublicAnnouncementListView,
)
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
from config.sitemaps import sitemaps
from layout.views import (
    CMSContactInquiryViewSet,
    CMSDailyVerseViewSet,
    CMSHomepageLayoutViewSet,
    CMSMenuItemViewSet,
    CMSSiteSettingViewSet,
    CMSSocialLinkViewSet,
    ContactInquiryCreateView,
    DailyVerseTodayView,
    PublicHomepageLayoutView,
    PublicMenuView,
    PublicSiteSettingView,
    PublicSocialLinkListView,
    SiteInquiryCreateView,
)
from media_library.views import CMSMediaAssetViewSet
from site_content.views import PublicSiteContentView
# Import views from our custom apps
from users.views import CMSUserViewSet, RegisterView, UserAuditLogViewSet, UserMeView

# ---------------------------------------------------------------------------
# Django Admin Site Customization
# ---------------------------------------------------------------------------
admin.site.site_header = "Christian Students Network Administration"
admin.site.site_title = "CSN Admin Portal"
admin.site.index_title = "Welcome to Christian Students Network Management"


# ---------------------------------------------------------------------------
# Deep Health check (Database + Cache readiness probe)
# ---------------------------------------------------------------------------

def health_check(request):
    """
    Verifies backend operational status including PostgreSQL and Cache.
    Returns 200 OK if healthy, 503 Service Unavailable if dependencies fail.
    """
    status_report = {'status': 'ok'}
    http_status = 200

    # 1. Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        status_report['database'] = 'ok'
    except Exception as exc:
        status_report['database'] = f'unhealthy: {exc}'
        status_report['status'] = 'error'
        http_status = 503

    # 2. Cache / Redis check
    try:
        cache.set('_probe', 1, timeout=5)
        if cache.get('_probe') == 1:
            status_report['cache'] = 'ok'
        else:
            status_report['cache'] = 'unresponsive'
            status_report['status'] = 'degraded'
    except Exception as exc:
        status_report['cache'] = f'unhealthy: {exc}'
        status_report['status'] = 'degraded'

    return JsonResponse(status_report, status=http_status)


# ---------------------------------------------------------------------------
# SEO Robots.txt
# ---------------------------------------------------------------------------

def robots_txt(request):
    admin_path = getattr(settings, 'ADMIN_URL', 'admin/').strip('/')
    lines = [
        "User-agent: *",
        f"Disallow: /{admin_path}/",
        "Disallow: /admin/",
        "Disallow: /api/v1/cms/",
        "Disallow: /api/v1/auth/",
        "Allow: /",
        "",
        "Sitemap: https://christianstudentsnetwork.org/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# ---------------------------------------------------------------------------
# CMS Router
# ---------------------------------------------------------------------------

cms_router = DefaultRouter()
cms_router.register(r'articles', CMSArticleViewSet, basename='cms-articles')
cms_router.register(r'categories', CMSCategoryViewSet, basename='cms-categories')
cms_router.register(r'tags', CMSTagViewSet, basename='cms-tags')
cms_router.register(r'comments', CMSCommentViewSet, basename='cms-comments')
cms_router.register(r'layout', CMSHomepageLayoutViewSet, basename='cms-layout')
cms_router.register(r'menus', CMSMenuItemViewSet, basename='cms-menus')
cms_router.register(r'daily-verses', CMSDailyVerseViewSet, basename='cms-daily-verses')
cms_router.register(r'announcements', CMSAnnouncementViewSet, basename='cms-announcements')
cms_router.register(r'settings', CMSSiteSettingViewSet, basename='cms-settings')
cms_router.register(r'contact-inquiries', CMSContactInquiryViewSet, basename='cms-contact-inquiries')
cms_router.register(r'media', CMSMediaAssetViewSet, basename='cms-media')
cms_router.register(r'social-links', CMSSocialLinkViewSet, basename='cms-social-links')
cms_router.register(r'users', CMSUserViewSet, basename='cms-users')
cms_router.register(r'user-audit-logs', UserAuditLogViewSet, basename='cms-user-audit-logs')


# ---------------------------------------------------------------------------
# URL patterns
# ---------------------------------------------------------------------------

admin_url_path = getattr(settings, 'ADMIN_URL', 'admin/').strip('/') + '/'

urlpatterns = [
    # Obfuscated Admin Interface (configurable via ADMIN_URL env var)
    path(admin_url_path, admin.site.urls),

    # SEO Endpoints
    path('robots.txt', robots_txt, name='robots-txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # Health check
    path('api/v1/health/', health_check, name='health-check'),

    # Auth endpoints
    path('api/v1/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/me/', UserMeView.as_view(), name='auth-me'),

    # Public Read endpoints
    path('api/v1/categories/', CategoryListView.as_view(), name='public-categories'),
    path('api/v1/tags/', TagListView.as_view(), name='public-tags'),
    path('api/v1/articles/', ArticleListView.as_view(), name='public-articles'),
    path('api/v1/articles/<slug:slug>/', ArticleDetailView.as_view(), name='public-article-detail'),
    path('api/v1/articles/<slug:slug>/comments/', ArticleCommentListView.as_view(), name='public-article-comments'),
    path('api/v1/articles/<slug:slug>/comments/create/', CommentCreateView.as_view(), name='public-create-comment'),
    path('api/v1/announcements/', PublicAnnouncementListView.as_view(), name='public-announcement-list'),
    path('api/v1/announcements/<int:pk>/', PublicAnnouncementDetailView.as_view(), name='public-announcement-detail'),
    path('api/v1/menus/', PublicMenuView.as_view(), name='public-menus'),

    # Contact Inquiries
    path('api/v1/contact/', ContactInquiryCreateView.as_view(), name='contact-inquiry-root'),
    path('api/v1/contact/inquiry/', ContactInquiryCreateView.as_view(), name='contact-inquiry'),
    path('api/v1/inquiries/', SiteInquiryCreateView.as_view(), name='site-inquiry'),

    # Fellowship site content (campuses, events, articles, statement of faith, ...)
    path('api/v1/site-content/', PublicSiteContentView.as_view(), name='public-site-content'),

    # Layout endpoints
    path('api/v1/homepage-layout/', PublicHomepageLayoutView.as_view(), name='public-homepage-layout'),
    path('api/v1/site-settings/', PublicSiteSettingView.as_view(), name='site-settings'),
    path('api/v1/daily-verse/today/', DailyVerseTodayView.as_view(), name='daily-verse-today'),
    path('api/v1/social-links/', PublicSocialLinkListView.as_view(), name='public-social-links'),

    # CMS Protected endpoints (Newsroom / Editorial Staff)
    path('api/v1/cms/', include(cms_router.urls)),
]

# ---------------------------------------------------------------------------
# Serve media files ONLY in development
# ---------------------------------------------------------------------------

if settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path

    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
