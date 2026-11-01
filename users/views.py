import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import UserAuditLog
from .permissions import IsAdmin
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    CMSUserSerializer,
    CMSUserCreateSerializer,
    UserAuditLogSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class CMSUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAdmin,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return CMSUserCreateSerializer
        return CMSUserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        UserAuditLog.objects.create(
            actor=self.request.user,
            target_user=user,
            action='create',
            details=f"Created user {user.username} with role {user.role}"
        )
        logger.info("User %s created by %s", user.username, self.request.user.username)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_role = old_instance.role
        old_active = old_instance.is_active

        user = serializer.save()

        details_parts = []
        if old_role != user.role:
            details_parts.append(f"Changed role from {old_role} to {user.role}")
            # Align is_staff status based on role
            user.is_staff = user.role in ('admin', 'editor', 'journalist')
            user.save(update_fields=['is_staff'])
        if old_active != user.is_active:
            status_str = "activated" if user.is_active else "deactivated"
            details_parts.append(f"Account {status_str}")

        other_changes = []
        for field in ('username', 'email', 'first_name', 'last_name', 'bio', 'twitter', 'github', 'website'):
            if getattr(old_instance, field) != getattr(user, field):
                other_changes.append(field)
        if other_changes:
            details_parts.append(f"Updated fields: {', '.join(other_changes)}")

        action_type = 'update'
        if old_role != user.role:
            action_type = 'role_change'
        elif old_active != user.is_active:
            action_type = 'status_change'

        details_str = "; ".join(details_parts) if details_parts else "Updated profile details"

        UserAuditLog.objects.create(
            actor=self.request.user,
            target_user=user,
            action=action_type,
            details=details_str,
        )
        logger.info("User %s updated by %s: %s", user.username, self.request.user.username, details_str)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if instance.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            return Response(
                {"detail": "Cannot delete the sole superuser."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.info("User %s deleted by %s", instance.username, request.user.username)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get('password')
        if not password:
            return Response(
                {"password": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate password against Django password validators
        try:
            validate_password(password, user=user)
        except DjangoValidationError as exc:
            return Response(
                {"password": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save(update_fields=['password'])

        UserAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action='password_reset',
            details="Reset user password",
        )
        logger.info("Password reset for %s by %s", user.username, request.user.username)
        return Response({"status": "Password reset successfully"}, status=status.HTTP_200_OK)


class UserAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserAuditLog.objects.select_related('actor', 'target_user').all()
    serializer_class = UserAuditLogSerializer
    permission_classes = (IsAdmin,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['target_user__username', 'target_user__email', 'actor__username', 'action', 'details']
    filterset_fields = ['action']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
