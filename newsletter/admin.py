from django.contrib import admin

from .models import NewsletterCampaign, Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    ordering = ('-subscribed_at',)
    list_per_page = 50

    actions = ['activate_subscribers', 'unsubscribe_subscribers']

    @admin.action(description="Activate selected subscribers")
    def activate_subscribers(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} subscriber(s) activated.")

    @admin.action(description="Unsubscribe selected subscribers")
    def unsubscribe_subscribers(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} subscriber(s) marked as inactive.")


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'created_at', 'sent_at')
    search_fields = ('subject', 'body')
    ordering = ('-created_at',)
    list_per_page = 25

