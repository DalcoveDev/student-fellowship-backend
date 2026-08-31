from django.contrib import admin

from .models import (
    ContactInquiry,
    DailyVerse,
    HomepageLayout,
    MenuItem,
    SiteSetting,
    SocialLink,
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = (
        'site_name',
        'contact_email',
        'contact_phone',
        'active_theme',
        'maintenance_mode',
    )

    fieldsets = (
        ('Brand & Identity', {
            'fields': ('site_name', 'logo_light', 'logo_dark', 'active_theme', 'footer_text'),
        }),
        ('Color Palette & Theme Overrides', {
            'fields': (
                'primary_color', 'secondary_color', 'font_color', 'bg_color',
                'btn_bg_color', 'btn_text_color', 'link_color', 'hover_color',
                'font_family_body', 'font_family_headings', 'custom_css',
            ),
            'classes': ('collapse',),
        }),
        ('Contact & Social Info', {
            'fields': (
                'contact_email', 'contact_phone', 'whatsapp_number', 'contact_address',
                'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url', 'linkedin_url', 'tiktok_url',
            ),
        }),
        ('Maintenance Mode', {
            'fields': ('maintenance_mode', 'maintenance_message', 'maintenance_contact_email'),
        }),
        ('Feed & Pagination Limits', {
            'fields': ('homepage_limit', 'footer_recent_limit'),
        }),
    )

    def has_add_permission(self, request):
        # Prevent creating multiple SiteSetting rows
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HomepageLayout)
class HomepageLayoutAdmin(admin.ModelAdmin):
    list_display = ('order', 'page', 'section_type', 'title', 'is_visible', 'article_limit')
    list_display_links = ('section_type', 'title')
    list_filter = ('page', 'section_type', 'is_visible')
    search_fields = ('title', 'content')
    ordering = ('order',)
    list_editable = ('order', 'is_visible')
    filter_horizontal = ('categories',)
    list_per_page = 30


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'menu_type', 'parent', 'order', 'is_visible', 'target_url_display')
    list_filter = ('position', 'menu_type', 'is_visible')
    search_fields = ('title', 'title_rw', 'title_fr', 'custom_url', 'page_slug')
    ordering = ('position', 'order', 'id')
    list_editable = ('order', 'is_visible')
    list_per_page = 50

    def target_url_display(self, obj):
        return obj.target_url
    target_url_display.short_description = "Target URL"


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'name', 'email', 'phone', 'subject', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')
    ordering = ('-created_at',)
    list_editable = ('is_read',)
    list_per_page = 30

    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description="Mark selected inquiries as read")
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"{count} inquiry(ies) marked as read.")

    @admin.action(description="Mark selected inquiries as unread")
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f"{count} inquiry(ies) marked as unread.")


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('platform', 'custom_name', 'url', 'order')
    list_filter = ('platform',)
    ordering = ('order',)
    list_editable = ('order',)


@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display = ('date', 'verse_reference', 'kinyarwanda_preview', 'english_preview')
    search_fields = ('verse_reference', 'verse_text_kinyarwanda', 'verse_text_english')
    ordering = ('-date',)
    list_per_page = 30

    def kinyarwanda_preview(self, obj):
        text = obj.verse_text_kinyarwanda
        return (text[:50] + '...') if len(text) > 50 else text
    kinyarwanda_preview.short_description = "Kinyarwanda"

    def english_preview(self, obj):
        text = obj.verse_text_english
        return (text[:50] + '...') if len(text) > 50 else text
    english_preview.short_description = "English"

