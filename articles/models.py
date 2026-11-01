import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from simple_history.models import HistoricalRecords


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    color_accent = models.CharField(max_length=7, default='#2F6DF6')  # Hex code
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    def __str__(self):
        return self.name


class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=500, blank=True)
    body = models.TextField()  # Stored as JSON or rich text/markdown
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_articles')
    co_authors = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='co_authored_articles')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    is_breaking = models.BooleanField(default=False, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_premium = models.BooleanField(default=False)

    reading_time = models.PositiveIntegerField(default=0)  # in minutes
    view_count = models.PositiveIntegerField(default=0)

    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)

    history = HistoricalRecords()  # audit logs for edits

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at'], name='idx_article_status_pub'),
            models.Index(fields=['category', 'status'], name='idx_article_cat_status'),
        ]

    def __str__(self):
        return self.title

    @classmethod
    def publish_due_scheduled(cls):
        """Promote scheduled articles whose release time has arrived.

        Called by the public list/detail views so scheduling works even when a
        Celery worker/beat process is not running.
        """
        return cls.objects.filter(
            status='scheduled',
            published_at__lte=timezone.now(),
        ).update(status='published')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Calculate reading time (roughly 200 words per minute)
        word_count = len(self.body.split()) if self.body else 0
        self.reading_time = max(1, round(word_count / 200))

        now = timezone.now()
        original_status = self.status

        # Keep status and publication time consistent:
        # - published without a date gets "now"
        # - published with a future date is effectively scheduled
        # - scheduled with a date that has passed is published immediately
        if self.status == 'published':
            if not self.published_at:
                self.published_at = now
            elif self.published_at > now:
                self.status = 'scheduled'
        elif self.status == 'scheduled' and self.published_at and self.published_at <= now:
            self.status = 'published'

        # Keep update_fields accurate when save() flips the status.
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and self.status != original_status:
            kwargs['update_fields'] = set(update_fields) | {'status'}

        super().save(*args, **kwargs)


class ArticleRevision(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='revisions')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Revision for '{self.article.title}' at {self.created_at}"


class Comment(models.Model):
    MODERATION_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('flagged', 'Flagged'),
        ('spam', 'Spam'),
    )

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    body = models.TextField()
    status = models.CharField(max_length=20, choices=MODERATION_CHOICES, default='approved', db_index=True)
    anonymous_identifier = models.CharField(max_length=40, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.article.title}"

    def save(self, *args, **kwargs):
        if not self.anonymous_identifier:
            # Use UUID-based identifier instead of random loop
            self.anonymous_identifier = f"COM{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
