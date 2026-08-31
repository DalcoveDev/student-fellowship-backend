from django.contrib import admin
from django.utils import timezone
from simple_history.admin import SimpleHistoryAdmin

from .models import Article, ArticleRevision, Category, Comment, Tag


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('user', 'body', 'status', 'created_at')
    readonly_fields = ('user', 'body', 'created_at')
    can_delete = True


class ArticleRevisionInline(admin.TabularInline):
    model = ArticleRevision
    extra = 0
    fields = ('author', 'title', 'created_at')
    readonly_fields = ('author', 'title', 'created_at')
    can_delete = False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color_accent', 'parent', 'order', 'articles_count')
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    def articles_count(self, obj):
        return obj.articles.count()
    articles_count.short_description = "Articles"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'articles_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def articles_count(self, obj):
        return obj.articles.count()
    articles_count.short_description = "Tagged Articles"


@admin.register(Article)
class ArticleAdmin(SimpleHistoryAdmin):
    list_display = (
        'title',
        'category',
        'author',
        'status',
        'is_featured',
        'is_breaking',
        'is_premium',
        'view_count',
        'reading_time',
        'published_at',
    )
    list_filter = ('status', 'category', 'is_featured', 'is_breaking', 'is_premium', 'created_at', 'published_at')
    search_fields = ('title', 'subtitle', 'body', 'author__username', 'author__email')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('category', 'author', 'tags', 'co_authors')
    readonly_views = ('view_count', 'reading_time', 'created_at', 'updated_at')
    readonly_fields = ('view_count', 'reading_time', 'created_at', 'updated_at')
    filter_horizontal = ('tags', 'co_authors')
    inlines = [CommentInline, ArticleRevisionInline]
    date_hierarchy = 'published_at'
    list_per_page = 25

    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'subtitle', 'body', 'cover_image', 'category', 'tags'),
        }),
        ('Authorship', {
            'fields': ('author', 'co_authors'),
        }),
        ('Publication & Visibility', {
            'fields': ('status', 'published_at', 'is_featured', 'is_breaking', 'is_premium'),
        }),
        ('SEO & Discovery', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',),
        }),
        ('Metrics & Timestamps', {
            'fields': ('view_count', 'reading_time', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['publish_articles', 'draft_articles', 'archive_articles', 'mark_featured', 'mark_breaking']

    @admin.action(description="Publish selected articles")
    def publish_articles(self, request, queryset):
        count = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f"{count} article(s) published successfully.")

    @admin.action(description="Set selected articles to Draft")
    def draft_articles(self, request, queryset):
        count = queryset.update(status='draft')
        self.message_user(request, f"{count} article(s) set to draft.")

    @admin.action(description="Archive selected articles")
    def archive_articles(self, request, queryset):
        count = queryset.update(status='archived')
        self.message_user(request, f"{count} article(s) archived.")

    @admin.action(description="Mark selected articles as Featured")
    def mark_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f"{count} article(s) marked as featured.")

    @admin.action(description="Mark selected articles as Breaking News")
    def mark_breaking(self, request, queryset):
        count = queryset.update(is_breaking=True)
        self.message_user(request, f"{count} article(s) marked as breaking.")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'status', 'created_at', 'body_summary')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'article__title', 'body', 'anonymous_identifier')
    autocomplete_fields = ('article', 'user')
    ordering = ('-created_at',)
    list_per_page = 50

    def body_summary(self, obj):
        return (obj.body[:60] + '...') if len(obj.body) > 60 else obj.body
    body_summary.short_description = "Comment"

    actions = ['approve_comments', 'mark_pending', 'mark_spam', 'flag_comments']

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        count = queryset.update(status='approved')
        self.message_user(request, f"{count} comment(s) approved.")

    @admin.action(description="Mark selected comments as Pending Review")
    def mark_pending(self, request, queryset):
        count = queryset.update(status='pending')
        self.message_user(request, f"{count} comment(s) marked as pending review.")

    @admin.action(description="Mark selected comments as Spam")
    def mark_spam(self, request, queryset):
        count = queryset.update(status='spam')
        self.message_user(request, f"{count} comment(s) marked as spam.")

    @admin.action(description="Flag selected comments for review")
    def flag_comments(self, request, queryset):
        count = queryset.update(status='flagged')
        self.message_user(request, f"{count} comment(s) flagged.")


@admin.register(ArticleRevision)
class ArticleRevisionAdmin(admin.ModelAdmin):
    list_display = ('article', 'author', 'title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'body', 'article__title', 'author__username')
    readonly_fields = ('article', 'author', 'title', 'subtitle', 'body', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False
