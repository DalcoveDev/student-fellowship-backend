from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SuperAdminDashboardStatsView,
    SuperAdminUserViewSet,
    GroupViewSet,
    PermissionListView,
    SystemAuditLogViewSet,
    SuperAdminSettingsView,
    SuperAdminToggleMaintenanceView,
)

router = DefaultRouter()
router.register(r'users', SuperAdminUserViewSet, basename='superadmin-users')
router.register(r'groups', GroupViewSet, basename='superadmin-groups')
router.register(r'logs', SystemAuditLogViewSet, basename='superadmin-logs')

urlpatterns = [
    path('stats/', SuperAdminDashboardStatsView.as_view(), name='superadmin-stats'),
    path('settings/', SuperAdminSettingsView.as_view(), name='superadmin-settings'),
    path('settings/toggle-maintenance/', SuperAdminToggleMaintenanceView.as_view(), name='superadmin-toggle-maintenance'),
    path('permissions/', PermissionListView.as_view(), name='superadmin-permissions'),
    path('', include(router.urls)),
]

