from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserAuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'avatar', 'bio')}),
        (_('Social Profiles'), {'fields': ('twitter', 'github', 'website'), 'classes': ('collapse',)}),
        (_('Platform Role & Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    actions = ['activate_users', 'deactivate_users', 'make_journalists', 'make_editors']

    @admin.action(description="Activate selected user accounts")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} user account(s) activated successfully.")

    @admin.action(description="Deactivate selected user accounts")
    def deactivate_users(self, request, queryset):
        # Prevent deactivating self
        if queryset.filter(pk=request.user.pk).exists():
            self.message_user(request, "You cannot deactivate your own account.", level='ERROR')
            queryset = queryset.exclude(pk=request.user.pk)
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} user account(s) deactivated.")

    @admin.action(description="Set selected users role to Journalist (staff)")
    def make_journalists(self, request, queryset):
        count = queryset.update(role='journalist', is_staff=True)
        self.message_user(request, f"{count} user(s) set to Journalist with staff access.")

    @admin.action(description="Set selected users role to Editor (staff)")
    def make_editors(self, request, queryset):
        count = queryset.update(role='editor', is_staff=True)
        self.message_user(request, f"{count} user(s) set to Editor with staff access.")


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action', 'target_user', 'details_summary')
    list_filter = ('action', 'timestamp')
    search_fields = ('actor__username', 'target_user__username', 'details')
    readonly_fields = ('actor', 'target_user', 'action', 'details', 'timestamp')
    ordering = ('-timestamp',)
    list_per_page = 50

    def details_summary(self, obj):
        return (obj.details[:75] + '...') if len(obj.details) > 75 else obj.details
    details_summary.short_description = "Details"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
