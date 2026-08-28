import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SystemAuditLog
from .permissions import IsSuperAdmin
from .serializers import (
    GroupSerializer,
    PermissionSerializer,
    SuperAdminSiteSettingSerializer,
    SuperAdminUserCreateSerializer,
    SuperAdminUserSerializer,
    SystemAuditLogSerializer,
)
from ads.models import AdSlot
from announcements.models import Announcement
from articles.models import Article, Category, Comment, Tag
from layout.models import ContactInquiry, SiteSetting
from media_library.models import MediaAsset
from newsletter.models import NewsletterCampaign, Subscriber

User = get_user_model()
logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class SuperAdminDashboardStatsView(APIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        user_counts = User.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            inactive=Count('id', filter=Q(is_active=False)),
            readers=Count('id', filter=Q(role='reader')),
            journalists=Count('id', filter=Q(role='journalist')),
            editors=Count('id', filter=Q(role='editor')),
            admins=Count('id', filter=Q(role='admin')),
            staff=Count('id', filter=Q(is_staff=True)),
            superusers=Count('id', filter=Q(is_superuser=True)),
            new_7d=Count('id', filter=Q(date_joined__gte=seven_days_ago)),
            new_30d=Count('id', filter=Q(date_joined__gte=thirty_days_ago)),
        )

        article_stats = Article.objects.aggregate(
            total=Count('id'),
            published=Count('id', filter=Q(status='published')),
            drafts=Count('id', filter=Q(status='draft')),
            scheduled=Count('id', filter=Q(status='scheduled')),
            rejected=Count('id', filter=Q(status='rejected')),
            total_views=Sum('view_count'),
            new_7d=Count('id', filter=Q(created_at__gte=seven_days_ago)),
        )

        category_count = Category.objects.count()
        tag_count = Tag.objects.count()
        comment_count = Comment.objects.count()
        pending_comments = Comment.objects.filter(status='pending').count()
        media_count = MediaAsset.objects.count()
        announcement_count = Announcement.objects.count()

        subscriber_count = Subscriber.objects.count()
        active_ads = AdSlot.objects.filter(is_active=True).count()
        total_campaigns = NewsletterCampaign.objects.count()
        total_inquiries = ContactInquiry.objects.count()
        pending_inquiries = ContactInquiry.objects.filter(is_read=False).count()

        setting = SiteSetting.objects.first()
        maintenance_mode = setting.maintenance_mode if setting else False
        active_theme = setting.active_theme if setting else 'theme-classic'
        site_name = setting.site_name if setting else 'Isezerano'

        recent_logs = SystemAuditLog.objects.select_related('actor')[:10]
        recent_logs_data = SystemAuditLogSerializer(recent_logs, many=True).data

        payload = {
            'overview': {
                'total_users': user_counts['total'] or 0,
                'active_users': user_counts['active'] or 0,
                'inactive_users': user_counts['inactive'] or 0,
                'new_users_7d': user_counts['new_7d'] or 0,
                'total_articles': article_stats['total'] or 0,
                'published_articles': article_stats['published'] or 0,
                'total_views': article_stats['total_views'] or 0,
                'total_subscribers': subscriber_count,
                'active_ads': active_ads,
                'pending_inquiries': pending_inquiries,
            },
            'user_roles': {
                'readers': user_counts['readers'] or 0,
                'journalists': user_counts['journalists'] or 0,
                'editors': user_counts['editors'] or 0,
                'admins': user_counts['admins'] or 0,
                'staff': user_counts['staff'] or 0,
                'superusers': user_counts['superusers'] or 0,
            },
            'articles_breakdown': {
                'total': article_stats['total'] or 0,
                'published': article_stats['published'] or 0,
                'drafts': article_stats['drafts'] or 0,
                'scheduled': article_stats['scheduled'] or 0,
                'rejected': article_stats['rejected'] or 0,
                'new_7d': article_stats['new_7d'] or 0,
            },
            'content_metrics': {
                'categories': category_count,
                'tags': tag_count,
                'comments': comment_count,
                'pending_comments': pending_comments,
                'media_assets': media_count,
                'announcements': announcement_count,
                'campaigns': total_campaigns,
                'inquiries': total_inquiries,
            },
            'platform_status': {
                'site_name': site_name,
                'maintenance_mode': maintenance_mode,
                'active_theme': active_theme,
                'server_time': now.isoformat(),
            },
            'recent_audit_logs': recent_logs_data,
        }

        return Response(payload, status=status.HTTP_200_OK)


class SuperAdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related('groups').all()
    permission_classes = (IsSuperAdmin,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_login', 'username', 'role']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return SuperAdminUserCreateSerializer
        return SuperAdminUserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        ip = get_client_ip(self.request)
        SystemAuditLog.objects.create(
            actor=self.request.user,
            action='USER_CREATE',
            target_model='User',
            target_id=str(user.id),
            details=f"Created user account '{user.username}' with role '{user.role}'",
            ip_address=ip,
        )
        logger.info("Superadmin %s created user %s", self.request.user.username, user.username)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_role = old_instance.role
        old_active = old_instance.is_active

        user = serializer.save()

        changes = []
        if old_role != user.role:
            changes.append(f"Role: {old_role} -> {user.role}")
            user.is_staff = user.role in ('admin', 'editor', 'journalist')
            user.save(update_fields=['is_staff'])
        if old_active != user.is_active:
            status_text = "Activated" if user.is_active else "Deactivated"
            changes.append(f"Status: {status_text}")

        for field in ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'bio'):
            if getattr(old_instance, field) != getattr(user, field):
                changes.append(f"Field '{field}' changed")

        details_str = "; ".join(changes) if changes else "Profile details updated"
        action_type = 'ROLE_CHANGE' if old_role != user.role else ('STATUS_CHANGE' if old_active != user.is_active else 'USER_UPDATE')

        ip = get_client_ip(self.request)
        SystemAuditLog.objects.create(
            actor=self.request.user,
            action=action_type,
            target_model='User',
            target_id=str(user.id),
            details=f"Updated user '{user.username}': {details_str}",
            ip_address=ip,
        )
        logger.info("Superadmin %s updated user %s: %s", self.request.user.username, user.username, details_str)

    def perform_destroy(self, instance):
        username = instance.username
        user_id = instance.id
        ip = get_client_ip(self.request)

        if instance == self.request.user:
            raise DjangoValidationError("You cannot delete your own superadmin account.")

        instance.delete()
        SystemAuditLog.objects.create(
            actor=self.request.user,
            action='ENTITY_DELETE',
            target_model='User',
            target_id=str(user_id),
            details=f"Deleted user account '{username}' (ID: {user_id})",
            ip_address=ip,
        )
        logger.info("Superadmin %s deleted user %s", self.request.user.username, username)

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get('password')
        if not password:
            return Response({'password': ['Password is required.']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            return Response({'password': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save(update_fields=['password'])

        ip = get_client_ip(request)
        SystemAuditLog.objects.create(
            actor=request.user,
            action='PASSWORD_RESET',
            target_model='User',
            target_id=str(user.id),
            details=f"Reset password for user '{user.username}'",
            ip_address=ip,
        )
        return Response({'status': f"Password for {user.username} has been reset successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({'error': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        state = 'activated' if user.is_active else 'deactivated'
        ip = get_client_ip(request)
        SystemAuditLog.objects.create(
            actor=request.user,
            action='STATUS_CHANGE',
            target_model='User',
            target_id=str(user.id),
            details=f"Account for user '{user.username}' was {state}",
            ip_address=ip,
        )
        return Response({'status': f"User account {state}.", 'is_active': user.is_active}, status=status.HTTP_200_OK)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.prefetch_related('permissions').all()
    serializer_class = GroupSerializer
    permission_classes = (IsSuperAdmin,)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def perform_create(self, serializer):
        group = serializer.save()
        ip = get_client_ip(self.request)
        SystemAuditLog.objects.create(
            actor=self.request.user,
            action='GROUP_CREATE',
            target_model='Group',
            target_id=str(group.id),
            details=f"Created role/group '{group.name}' with {group.permissions.count()} permissions",
            ip_address=ip,
        )

    def perform_update(self, serializer):
        group = serializer.save()
        ip = get_client_ip(self.request)
        SystemAuditLog.objects.create(
            actor=self.request.user,
            action='GROUP_UPDATE',
            target_model='Group',
            target_id=str(group.id),
            details=f"Updated role/group '{group.name}' (Permissions count: {group.permissions.count()})",
            ip_address=ip,
        )

    def perform_destroy(self, instance):
        name = instance.name
        group_id = instance.id
        ip = get_client_ip(self.request)
        instance.delete()
        SystemAuditLog.objects.create(
            actor=self.request.user,
            action='GROUP_DELETE',
            target_model='Group',
            target_id=str(group_id),
            details=f"Deleted role/group '{name}'",
            ip_address=ip,
        )


class PermissionListView(generics.ListAPIView):
    queryset = Permission.objects.select_related('content_type').all()
    serializer_class = PermissionSerializer
    permission_classes = (IsSuperAdmin,)
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'codename', 'content_type__app_label', 'content_type__model']
    filterset_fields = ['content_type__app_label']
    pagination_class = None


class SystemAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemAuditLog.objects.select_related('actor').all()
    serializer_class = SystemAuditLogSerializer
    permission_classes = (IsSuperAdmin,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'target_model']
    search_fields = ['actor__username', 'actor__email', 'details', 'ip_address', 'target_model', 'target_id']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']


class SuperAdminSettingsView(APIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        setting = SiteSetting.objects.first()
        if not setting:
            setting = SiteSetting.objects.create(site_name="Isezerano")
        serializer = SuperAdminSiteSettingSerializer(setting)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        setting = SiteSetting.objects.first()
        if not setting:
            setting = SiteSetting.objects.create(site_name="Isezerano")

        serializer = SuperAdminSiteSettingSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            ip = get_client_ip(request)
            SystemAuditLog.objects.create(
                actor=request.user,
                action='SETTINGS_UPDATE',
                target_model='SiteSetting',
                target_id=str(setting.id),
                details=f"Platform settings updated by {request.user.username}",
                ip_address=ip,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuperAdminToggleMaintenanceView(APIView):
    permission_classes = (IsSuperAdmin,)

    def post(self, request):
        setting = SiteSetting.objects.first()
        if not setting:
            setting = SiteSetting.objects.create(site_name="Isezerano")

        setting.maintenance_mode = not setting.maintenance_mode
        setting.save(update_fields=['maintenance_mode'])

        ip = get_client_ip(request)
        state_str = "ENABLED" if setting.maintenance_mode else "DISABLED"
        SystemAuditLog.objects.create(
            actor=request.user,
            action='MAINTENANCE_TOGGLE',
            target_model='SiteSetting',
            target_id=str(setting.id),
            details=f"Maintenance mode was {state_str}",
            ip_address=ip,
        )
        return Response(
            {
                'status': f"Maintenance mode {state_str}.",
                'maintenance_mode': setting.maintenance_mode,
            },
            status=status.HTTP_200_OK,
        )

