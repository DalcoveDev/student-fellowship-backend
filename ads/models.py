from django.db import models
from django.conf import settings
from articles.models import Article

class AdSlot(models.Model):
    PLACEMENT_CHOICES = (
        ('header_banner', 'Header Banner (970x90 Leaderboard)'),
        ('hero_sidebar', 'Hero Sidebar (300x600 Skyscraper)'),
        ('daily_verse_sidebar', 'Daily Verse Sidebar (300x250 Medium Rectangle)'),
        ('news_desk_sidebar', 'News Desk Sidebar (300x600 Skyscraper)'),
        ('full_width_1', 'Full Width Banner 1 (728x90)'),
        ('full_width_2', 'Full Width Banner 2 (728x90)'),
        ('full_width_3', 'Full Width Banner 3 (728x90)'),
        ('full_width_4', 'Full Width Banner 4 (728x90)'),
        ('sponsored_content', 'Sponsored Content Block (Tax Corner style)'),
        ('grid_sidebar_stack_1', 'Grid Sidebar Stack Ad 1 (300x250)'),
        ('grid_sidebar_stack_2', 'Grid Sidebar Stack Ad 2 (300x250)'),
        ('grid_sidebar_stack_3', 'Grid Sidebar Stack Ad 3 (300x250)'),
        ('sports_sidebar', 'Sports Sidebar (300x600 Skyscraper)'),
        ('flyer_1', 'Flyer Ad 1 (Square/Portrait)'),
        ('flyer_2', 'Flyer Ad 2 (Square/Portrait)'),
        ('flyer_3', 'Flyer Ad 3 (Square/Portrait)'),
        
        # Legacy/Other Placements
        ('header-banner', 'Legacy Header Banner (970x250)'),
        ('sidebar-rail', 'Legacy Sidebar Rail (300x600)'),
        ('in-feed-native', 'Legacy In-Feed Native Ad Card'),
        ('in-article-inline', 'Legacy In-Article Inline (336x280)'),
        ('footer-banner', 'Legacy Footer Banner (728x90)'),
        ('interstitial', 'Legacy Interstitial Modal (Glass popup)'),
    )

    name = models.CharField(max_length=100)
    placement = models.CharField(max_length=30, choices=PLACEMENT_CHOICES)
    image = models.ImageField(upload_to='ads/', null=True, blank=True)
    html_content = models.TextField(blank=True, help_text="For custom HTML/JS ad codes like Google Adsense")
    target_url = models.URLField(blank=True)
    cta_text = models.CharField(max_length=50, default='Learn More')
    
    # Sponsored Rich Content fields
    sponsored_logo = models.ImageField(upload_to='ads/logos/', null=True, blank=True)
    sponsored_headline = models.CharField(max_length=255, blank=True)
    sponsored_video_url = models.URLField(blank=True, help_text="For sponsored video embed block")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    priority = models.PositiveIntegerField(default=0, help_text="Higher priority ads are served first")
    
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.get_placement_display()}"

    @property
    def ctr(self):
        if self.impressions == 0:
            return 0.0
        return round((self.clicks / self.impressions) * 100, 2)

class AnalyticsEvent(models.Model):
    EVENT_TYPE_CHOICES = (
        ('pageview', 'Page View'),
        ('ad_impression', 'Ad Impression'),
        ('ad_click', 'Ad Click'),
    )

    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')
    ad_slot = models.ForeignKey(AdSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_event_type_display()} at {self.created_at}"
