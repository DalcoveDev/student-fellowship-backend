from django.contrib import admin
from django.utils.html import format_html

from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'preview', 'file_name', 'uploaded_at')
    search_fields = ('title', 'caption', 'alt_text', 'file')
    ordering = ('-uploaded_at',)
    list_per_page = 30

    def file_name(self, obj):
        return obj.file.name.split('/')[-1]
    file_name.short_description = "Filename"

    def preview(self, obj):
        if obj.file and any(obj.file.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
            return format_html('<img src="{}" style="max-height: 40px; border-radius: 4px;" />', obj.file.url)
        return "📄 File"
    preview.short_description = "Preview"
