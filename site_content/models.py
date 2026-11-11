"""Content models for the Christian Students Network website.

The public serializer output mirrors the shape the Next.js frontend renders, so
the API can be swapped in for the frontend's local content modules without
changing component code.
"""
from django.core.exceptions import ValidationError
from django.db import models


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ['order', 'id']


class SiteProfile(models.Model):
    """Singleton with the site identity, contact details, and navigation.

    ``phones``, ``join_phone``, ``socials``, and ``nav`` are stored as JSON
    because they are small display structures rather than queryable records.
    """

    name = models.CharField(max_length=120, default='Christian Students Network')
    short_name = models.CharField(max_length=30, default='CSN')
    tagline = models.CharField(max_length=255, blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    site_url = models.URLField(blank=True)
    phones = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"label", "href"} phone entries.',
    )
    join_phone = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"label", "href"} shown on the join page.',
    )
    socials = models.JSONField(default=dict, blank=True)
    nav = models.JSONField(
        default=list,
        blank=True,
        help_text='Header navigation items with optional children.',
    )

    class Meta:
        verbose_name = 'Site Profile'
        verbose_name_plural = 'Site Profile'

    def save(self, *args, **kwargs):
        if not self.pk and SiteProfile.objects.exists():
            raise ValidationError('There can only be one Site Profile instance.')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MinistryExpression(OrderedModel):
    number = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    description = models.TextField()
    href = models.CharField(max_length=255, blank=True)
    image = models.CharField(max_length=255, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Ministry Expression'
        verbose_name_plural = 'Ministry Expressions'

    def __str__(self):
        return f'{self.number} — {self.title}'


class Campus(OrderedModel):
    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, blank=True)
    campus_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    detail = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Campus'
        verbose_name_plural = 'Campuses'

    def __str__(self):
        return self.name


class SiteEvent(OrderedModel):
    day = models.CharField(max_length=10)
    month = models.CharField(max_length=20)
    date_label = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f'{self.date_label} — {self.title}'


class ThursdaySession(OrderedModel):
    session = models.CharField(max_length=50)
    time = models.CharField(max_length=100)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Thursday Session'
        verbose_name_plural = 'Thursday Sessions'

    def __str__(self):
        return f'{self.session} ({self.time})'


class GalleryImage(OrderedModel):
    src = models.CharField(max_length=255)
    alt = models.CharField(max_length=255)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery'

    def __str__(self):
        return self.title


class Testimonial(OrderedModel):
    quote = models.TextField()
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f'{self.name} ({self.role})'


class LeadershipTeam(OrderedModel):
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    responsibilities = models.JSONField(default=list, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Leadership Team'
        verbose_name_plural = 'Leadership Teams'

    def __str__(self):
        return self.title


class FaithSection(OrderedModel):
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=200)
    paragraphs = models.JSONField(default=list, blank=True)
    scripture = models.TextField(blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Statement of Faith Section'
        verbose_name_plural = 'Statement of Faith'

    def __str__(self):
        return self.title


class SiteArticle(OrderedModel):
    """Teaching article rendered by the frontend's article pages.

    Kept separate from ``articles.Article`` (the news CMS) because the
    fellowship's teaching library has a structured section body rather than a
    flat news body.
    """

    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    excerpt = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)
    image_alt = models.CharField(max_length=255, blank=True)
    sections = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"heading"?: str, "paragraphs": [str]} sections.',
    )
    scripture = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text='{"text", "reference"} pull quote, or null.',
    )

    class Meta(OrderedModel.Meta):
        verbose_name = 'Site Article'
        verbose_name_plural = 'Site Articles'

    def __str__(self):
        return self.title
