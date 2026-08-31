from django.contrib import admin

from .models import AdSlot, AnalyticsEvent


@admin.register(AdSlot)
class AdSlotAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'placement',
        'is_active',
        'priority',
        'impressions',
        'clicks',
        'ctr_display',
        'start_date',
        'end_date',
    )
    list_filter = ('placement', 'is_active', 'start_date', 'end_date')
    search_fields = ('name', 'sponsored_headline', 'target_url')
    ordering = ('-priority', '-start_date')
    list_per_page = 25

    fieldsets = (
        ('Campaign Info', {
            'fields': ('name', 'placement', 'is_active', 'priority', 'start_date', 'end_date'),
        }),
        ('Creative & Content', {
            'fields': ('image', 'target_url', 'cta_text', 'html_content'),
        }),
        ('Sponsored Video & Logo', {
            'fields': ('sponsored_logo', 'sponsored_headline', 'sponsored_video_url'),
            'classes': ('collapse',),
        }),
        ('Metrics', {
            'fields': ('impressions', 'clicks'),
        }),
    )

    def ctr_display(self, obj):
        return f"{obj.ctr}%"
    ctr_display.short_description = "CTR (%)"

    actions = ['activate_ads', 'deactivate_ads', 'reset_metrics']

    @admin.action(description="Activate selected ad slots")
    def activate_ads(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} ad slot(s) activated.")

    @admin.action(description="Deactivate selected ad slots")
    def deactivate_ads(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} ad slot(s) deactivated.")

    @admin.action(description="Reset impressions and clicks counters")
    def reset_metrics(self, request, queryset):
        count = queryset.update(impressions=0, clicks=0)
        self.message_user(request, f"Metrics reset for {count} ad slot(s).")


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'article', 'ad_slot', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('ip_address', 'article__title', 'ad_slot__name', 'user_agent')
    readonly_fields = ('event_type', 'article', 'ad_slot', 'ip_address', 'user_agent', 'referrer', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

