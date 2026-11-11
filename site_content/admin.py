from django.contrib import admin

from .models import (
    Campus,
    FaithSection,
    GalleryImage,
    LeadershipTeam,
    MinistryExpression,
    SiteArticle,
    SiteEvent,
    SiteProfile,
    Testimonial,
    ThursdaySession,
)


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'email', 'location')

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MinistryExpression)
class MinistryExpressionAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'order')
    list_editable = ('order',)
    ordering = ('order',)


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'campus_type', 'slug', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)


@admin.register(SiteEvent)
class SiteEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_label', 'kind', 'order')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    ordering = ('order',)


@admin.register(ThursdaySession)
class ThursdaySessionAdmin(admin.ModelAdmin):
    list_display = ('session', 'time', 'order')
    list_editable = ('order',)
    ordering = ('order',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'src', 'order')
    list_editable = ('order',)
    list_filter = ('category',)
    search_fields = ('title', 'alt', 'src')
    ordering = ('order',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'role', 'quote')
    ordering = ('order',)


@admin.register(LeadershipTeam)
class LeadershipTeamAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    list_editable = ('order',)
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)


@admin.register(FaithSection)
class FaithSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    list_editable = ('order',)
    search_fields = ('title', 'paragraphs', 'scripture')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)


@admin.register(SiteArticle)
class SiteArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'slug', 'order')
    list_editable = ('order',)
    list_filter = ('category',)
    search_fields = ('title', 'slug', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)
