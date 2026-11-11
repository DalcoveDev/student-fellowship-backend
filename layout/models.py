from django.db import models
from django.core.exceptions import ValidationError
from articles.models import Category


class HomepageLayout(models.Model):
    SECTION_CHOICES = (
        ('hero', 'Hero Lead Story Section'),
        ('banner', 'Homepage Banner Section'),
        ('featured-grid', 'Secondary Featured Grid (3-4 stories)'),
        ('category-rail', 'Category Scroll Rail'),
        ('trending-widget', 'Trending & Popular List Sidebar'),
        ('news-desk', 'News Desk Section'),
        ('announcements', 'Amatangazo Classifieds Section'),
        ('lifestyle', 'Lifestyle & Culture Section'),
        ('sports-grid', 'Sports Vertical Grid Section'),
        ('featured-secondary', 'Second Featured Posts Row'),
        ('flyers', 'Local Partner Flyers Row'),
        ('you-missed', 'You Missed Scroll Rail'),
        ('video-widget', 'Video Widget (YouTube & External Player)'),
        ('rich-text', 'Custom Rich Text Block / One-Pager'),
        ('one-pager', 'Company / Service One-Pager Section'),
        ('contact-form', 'Contact Inquiry Form'),
    )

    page = models.CharField(max_length=50, default='home', db_index=True)
    section_type = models.CharField(max_length=30, choices=SECTION_CHOICES)
    order = models.PositiveIntegerField(default=0)
    article_limit = models.PositiveIntegerField(
        default=5,
        null=True,
        blank=True,
        help_text="Number of articles to fetch for this section")

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True, help_text="HTML/markdown content for text sections or one-pagers")
    video_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Single or multiple comma-separated YouTube/video URLs for video widget")
    display_variant = models.CharField(
        max_length=50,
        blank=True,
        default='default',
        help_text="Visual variant / template")

    # Banner-specific fields
    banner_image = models.ImageField(
        upload_to='banners/',
        null=True,
        blank=True,
        help_text="Banner image for homepage banner section")
    banner_text = models.TextField(
        blank=True,
        help_text="Description/text displayed over or alongside the banner image")
    banner_show_description = models.BooleanField(
        default=True,
        help_text="Show the banner description by default on the public page")

    # Specific fields for conditional sections
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                 blank=True, help_text="Legacy single category reference")
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='layout_sections',
        help_text="One or multiple categories to fetch content from")

    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Page Section"
        verbose_name_plural = "Page Sections"

    def __str__(self):
        desc = self.get_section_type_display()
        if self.section_type == 'category-rail' and self.category:
            desc += f" ({self.category.name})"
        return f"{self.page} - {self.order}. {desc}"


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=100, default='Isezerano')
    logo_light = models.ImageField(upload_to='settings/', null=True, blank=True)
    logo_dark = models.ImageField(upload_to='settings/', null=True, blank=True)

    # Color overrides
    primary_color = models.CharField(max_length=7, default='#2F6DF6')
    secondary_color = models.CharField(max_length=7, default='#F0F4FF')
    font_color = models.CharField(max_length=7, default='#0F1117')
    bg_color = models.CharField(max_length=7, default='#FFFFFF')
    btn_bg_color = models.CharField(max_length=7, default='#062360')
    btn_text_color = models.CharField(max_length=7, default='#FFFFFF')
    link_color = models.CharField(max_length=7, default='#062360')
    hover_color = models.CharField(max_length=7, default='#0A3490')

    # Typography
    font_family_body = models.CharField(max_length=100, default='Inter')
    font_family_headings = models.CharField(max_length=100, default='Playfair Display')

    # Theme
    active_theme = models.CharField(max_length=50, default='theme-classic')
    custom_css = models.TextField(blank=True, default='')

    # Maintenance Mode
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        default=(
            "We are currently performing scheduled system updates and "
            "maintenance. We will be back online shortly."
        ),
    )
    maintenance_contact_email = models.EmailField(blank=True, default="contact@isezerano.com")

    # Contact Information
    contact_phone = models.CharField(max_length=50, blank=True, default="+250 788 000 000")
    contact_email = models.EmailField(blank=True, default="info@isezerano.rw")
    contact_address = models.CharField(max_length=255, blank=True, default="Kigali, Rwanda")
    whatsapp_number = models.CharField(max_length=50, blank=True, default="+250 788 000 000")

    # Direct Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)

    footer_text = models.TextField(blank=True, default="© 2026 Isezerano. Futuristic Digital Journalism.")
    footer_recent_limit = models.PositiveIntegerField(default=3)
    homepage_limit = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def save(self, *args, **kwargs):
        if not self.pk and SiteSetting.objects.exists():
            raise ValidationError("There can only be one SiteSetting instance.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.site_name} Settings"


class MenuItem(models.Model):
    MENU_TYPE_CHOICES = (
        ('custom', 'Custom Link'),
        ('page', 'Internal Page'),
        ('category', 'Category Archive'),
        ('article', 'Specific Article'),
        ('external', 'External URL'),
    )

    POSITION_CHOICES = (
        ('header_main', 'Main Navigation Bar (Header)'),
        ('header_top', 'Top Utility Bar'),
        ('footer_quick_links', 'Footer Quick Links'),
        ('footer_legal', 'Footer Legal / Secondary'),
    )

    title = models.CharField(max_length=100, help_text="Default display title (English)")
    title_rw = models.CharField(max_length=100, blank=True, help_text="Kinyarwanda translation")
    title_fr = models.CharField(max_length=100, blank=True, help_text="French translation")

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent menu item for sub-menus and sub-sub-menus"
    )

    menu_type = models.CharField(max_length=20, choices=MENU_TYPE_CHOICES, default='custom')
    page_slug = models.CharField(
        max_length=100,
        blank=True,
        help_text="Page route (e.g. home, about-us, services, contact, blog-feed)")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='menu_items')
    article_slug = models.CharField(max_length=255, blank=True, help_text="Slug of the article to link to")
    custom_url = models.CharField(max_length=500, blank=True, help_text="Internal path or full external URL")

    position = models.CharField(max_length=30, choices=POSITION_CHOICES, default='header_main')
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)
    icon_name = models.CharField(max_length=50, blank=True, help_text="Optional icon identifier")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"

    def __str__(self):
        prefix = "— " * self.get_depth()
        return f"{prefix}{self.title} ({self.position})"

    def get_depth(self):
        depth = 0
        p = self.parent
        while p is not None:
            depth += 1
            p = p.parent
        return depth

    @property
    def target_url(self):
        if self.menu_type == 'page':
            if not self.page_slug or self.page_slug in ['home', '/']:
                return '/'
            return f"/{self.page_slug.lstrip('/')}"
        elif self.menu_type == 'category' and self.category:
            return f"/c/{self.category.slug}"
        elif self.menu_type == 'article' and self.article_slug:
            return f"/a/{self.article_slug}"
        elif self.custom_url:
            return self.custom_url
        return '/'


class ContactInquiry(models.Model):
    KIND_CHOICES = (
        ('contact', 'Contact message'),
        ('join', 'Bible study enquiry'),
        ('visit', 'Visit plan'),
    )

    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='contact', db_index=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    contact = models.CharField(
        max_length=200, blank=True,
        help_text="Phone or email supplied through the join or visit form")
    campus = models.CharField(max_length=200, blank=True)
    session = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"Inquiry from {self.name} - {self.subject}"


class SocialLink(models.Model):
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter/X'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('linkedin', 'LinkedIn'),
        ('custom', 'Custom Platform'),
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='custom')
    custom_name = models.CharField(max_length=50, blank=True, help_text="Required for custom platform")
    url = models.URLField()
    icon_name = models.CharField(
        max_length=30,
        default='link',
        help_text="Lucide icon name (e.g. facebook, twitter, instagram, link)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        if self.platform == 'custom':
            return f"{self.custom_name}: {self.url}"
        return f"{self.platform}: {self.url}"


class DailyVerse(models.Model):
    date = models.DateField(unique=True, help_text="Date for which this verse is shown")
    verse_reference = models.CharField(max_length=255, help_text="e.g., Yohana 3:16 / John 3:16")
    verse_text_kinyarwanda = models.TextField(help_text="Verse text in Kinyarwanda")
    verse_text_english = models.TextField(help_text="Verse text in English")
    verse_text_french = models.TextField(blank=True, default='', help_text="Verse text in French")

    class Meta:
        ordering = ['-date']
        verbose_name = "Daily Verse"
        verbose_name_plural = "Daily Verses"

    def __str__(self):
        return f"{self.date} - {self.verse_reference}"
