"""
SEO sitemaps for the student fellowship site.
Includes standard Article sitemap, Static views sitemap, and Google News sitemap.
"""
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from articles.models import Article, Category


class ArticleSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Article.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).order_by('-published_at')

    def lastmod(self, obj):
        return obj.updated_at or obj.published_at

    def location(self, obj):
        return f"/a/{obj.slug}"


class GoogleNewsSitemap(Sitemap):
    """
    Google News sitemap: includes only articles published in the last 48 hours.
    Google News requires publication_date <= 48 hours old.
    """
    priority = 1.0
    protocol = "https"

    def items(self):
        cutoff = timezone.now() - timezone.timedelta(days=2)
        return Article.objects.filter(
            status='published',
            published_at__gte=cutoff,
            published_at__lte=timezone.now()
        ).order_by('-published_at')

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        return f"/a/{obj.slug}"


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Category.objects.all().order_by('order', 'id')

    def location(self, obj):
        return f"/c/{obj.slug}"


sitemaps = {
    'articles': ArticleSitemap,
    'news': GoogleNewsSitemap,
    'categories': CategorySitemap,
}
