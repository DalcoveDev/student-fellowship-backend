from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'announcement_type',
        'organization_name',
        'published_date',
        'deadline_date',
        'is_active',
    )
    list_filter = ('announcement_type', 'is_active', 'published_date')
    search_fields = ('title', 'organization_name', 'body', 'reference_number')
    ordering = ('-published_date', '-id')
    list_editable = ('is_active',)
    list_per_page = 30

    fieldsets = (
        ('Announcement Details', {
            'fields': ('title', 'announcement_type', 'organization_name', 'reference_number', 'body'),
        }),
        ('Dates & Status', {
            'fields': ('published_date', 'deadline_date', 'is_active', 'attachment'),
        }),
    )

    actions = ['activate_announcements', 'deactivate_announcements']

    @admin.action(description="Activate selected announcements")
    def activate_announcements(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} announcement(s) activated.")

    @admin.action(description="Deactivate selected announcements")
    def deactivate_announcements(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} announcement(s) deactivated.")
