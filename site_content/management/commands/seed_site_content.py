"""Load the website content snapshot into the database.

The JSON snapshot is generated from the frontend's content modules, so this
command keeps the API and the site's source content in step. Running it again
updates existing rows by their natural key instead of duplicating them.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from site_content.models import (
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

DATA_FILE = Path(__file__).resolve().parents[2] / 'data' / 'site_content.json'


class Command(BaseCommand):
    help = 'Seed the fellowship site content from data/site_content.json.'

    @transaction.atomic
    def handle(self, *args, **options):
        data = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        site = data['site']

        SiteProfile.objects.update_or_create(
            pk=1,
            defaults={
                'name': site['name'],
                'short_name': site['shortName'],
                'tagline': site.get('tagline', ''),
                'mission': site.get('mission', ''),
                'vision': site.get('vision', ''),
                'email': site.get('email', ''),
                'location': site.get('location', ''),
                'site_url': site.get('url', ''),
                'phones': site.get('phones', []),
                'join_phone': site.get('joinPhone', {}),
                'socials': site.get('socials', {}),
                'nav': data.get('nav', []),
            },
        )

        for order, item in enumerate(data.get('ministryExpressions', [])):
            MinistryExpression.objects.update_or_create(
                number=item['number'],
                defaults={
                    'title': item['title'],
                    'description': item['description'],
                    'href': item.get('href', ''),
                    'image': item.get('image', ''),
                    'image_alt': item.get('imageAlt', ''),
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('campuses', [])):
            Campus.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'name': item['name'],
                    'short_name': item.get('shortName', ''),
                    'campus_type': item.get('type', ''),
                    'description': item.get('description', ''),
                    'detail': item.get('detail', ''),
                    'image': item.get('image', ''),
                    'image_alt': item.get('imageAlt', ''),
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('events', [])):
            SiteEvent.objects.update_or_create(
                title=item['title'],
                defaults={
                    'day': item['day'],
                    'month': item['month'],
                    'date_label': item['dateLabel'],
                    'kind': item.get('kind', ''),
                    'description': item.get('description', ''),
                    'image': item.get('image', ''),
                    'image_alt': item.get('imageAlt', ''),
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('thursdaySessions', [])):
            ThursdaySession.objects.update_or_create(
                session=item['session'],
                defaults={'time': item['time'], 'order': order},
            )

        for order, item in enumerate(data.get('gallery', [])):
            GalleryImage.objects.update_or_create(
                src=item['src'],
                defaults={
                    'alt': item['alt'],
                    'title': item['title'],
                    'category': item['category'],
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('testimonials', [])):
            Testimonial.objects.update_or_create(
                name=item['name'],
                defaults={
                    'quote': item['quote'],
                    'role': item.get('role', ''),
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('leadershipTeams', [])):
            LeadershipTeam.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'title': item['title'],
                    'summary': item['summary'],
                    'responsibilities': item.get('responsibilities', []),
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('statementOfFaith', [])):
            FaithSection.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'title': item['title'],
                    'paragraphs': item.get('paragraphs', []),
                    'scripture': item.get('scripture', ''),
                    'order': order,
                },
            )

        for order, item in enumerate(data.get('articles', [])):
            SiteArticle.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'title': item['title'],
                    'category': item.get('category', ''),
                    'excerpt': item.get('excerpt', ''),
                    'image': item.get('image', ''),
                    'image_alt': item.get('imageAlt', ''),
                    'sections': item.get('sections', []),
                    'scripture': item.get('scripture'),
                    'order': order,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            'Seeded site content: '
            f'{len(data.get("campuses", []))} campuses, '
            f'{len(data.get("events", []))} events, '
            f'{len(data.get("gallery", []))} gallery images, '
            f'{len(data.get("articles", []))} articles.'
        ))
