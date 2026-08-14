"""
URL configuration for Isezerano project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import views from our custom apps
from users.views import RegisterView, UserMeView, CMSUserViewSet, UserAuditLogViewSet
from articles.views import (
    CategoryListView, TagListView, ArticleListView, ArticleDetailView,
    CommentCreateView, ArticleCommentListView,
    CMSArticleViewSet, CMSCategoryViewSet, CMSTagViewSet, CMSCommentViewSet,
)
from ads.views import ActiveAdView, TrackAnalyticsView, CMSAdSlotViewSet, RequestAdKitView
from newsletter.views import SubscribeView, CMSSubscriberViewSet, CMSNewsletterCampaignViewSet
from layout.views import (
    PublicHomepageLayoutView, PublicSiteSettingView, CMSHomepageLayoutViewSet,
    CMSSiteSettingViewSet, DailyVerseTodayView, CMSDailyVerseViewSet,
    CMSSocialLinkViewSet, PublicSocialLinkListView,
    ContactInquiryCreateView, CMSContactInquiryViewSet,
    PublicMenuView, CMSMenuItemViewSet,
)
from media_library.views import CMSMediaAssetViewSet
from announcements.views import (
    PublicAnnouncementListView, PublicAnnouncementDetailView, CMSAnnouncementViewSet,
)


# ---------------------------------------------------------------------------
# Health check (for Docker / load balancer readiness probes)
# ---------------------------------------------------------------------------

def health_check(request):
    return JsonResponse({'status': 'ok'})


# ---------------------------------------------------------------------------
# CMS Router
# ---------------------------------------------------------------------------

cms_router = DefaultRouter()
cms_router.register(r'articles', CMSArticleViewSet, basename='cms-articles')
cms_router.register(r'categories', CMSCategoryViewSet, basename='cms-categories')
cms_router.register(r'tags', CMSTagViewSet, basename='cms-tags')
cms_router.register(r'comments', CMSCommentViewSet, basename='cms-comments')
cms_router.register(r'ads', CMSAdSlotViewSet, basename='cms-ads')
cms_router.register(r'subscribers', CMSSubscriberViewSet, basename='cms-subscribers')
cms_router.register(r'campaigns', CMSNewsletterCampaignViewSet, basename='cms-campaigns')
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

urlpatterns = [
    path('admin/', admin.site.urls),

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

    # Ads & Analytics endpoints
    path('api/v1/ads/request-kit/', RequestAdKitView.as_view(), name='request-ad-kit'),
    path('api/v1/ads/<str:placement>/', ActiveAdView.as_view(), name='active-ad'),
    path('api/v1/analytics/track/', TrackAnalyticsView.as_view(), name='track-analytics'),

    # Contact Inquiries
    path('api/v1/contact/', ContactInquiryCreateView.as_view(), name='contact-inquiry-root'),
    path('api/v1/contact/inquiry/', ContactInquiryCreateView.as_view(), name='contact-inquiry'),

    # Newsletter & Layout endpoints
    path('api/v1/newsletter/subscribe/', SubscribeView.as_view(), name='newsletter-subscribe'),
    path('api/v1/homepage-layout/', PublicHomepageLayoutView.as_view(), name='public-homepage-layout'),
    path('api/v1/site-settings/', PublicSiteSettingView.as_view(), name='site-settings'),
    path('api/v1/daily-verse/today/', DailyVerseTodayView.as_view(), name='daily-verse-today'),
    path('api/v1/social-links/', PublicSocialLinkListView.as_view(), name='public-social-links'),

    # CMS Protected endpoints
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
