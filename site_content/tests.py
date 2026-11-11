from rest_framework import status
from rest_framework.test import APITestCase

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


class SiteContentApiTests(APITestCase):
    def setUp(self):
        SiteProfile.objects.create(
            pk=1,
            name='Christian Students Network',
            short_name='CSN',
            email='hello@example.com',
            site_url='https://christianstudentsnetwork.org',
            phones=[{'label': '0784 857 707', 'href': 'tel:+250784857707'}],
            join_phone={'label': '+250 784 857 707', 'href': 'tel:+250784857707'},
            socials={'youtube': 'https://youtube.com/example'},
            nav=[{'label': 'About', 'href': '/about'}],
        )
        MinistryExpression.objects.create(
            number='01',
            title='Weekly discipleship classes',
            description='Weekly groups.',
            image='/images/bible-study-smallgroup.webp',
            image_alt='Students in a small group',
        )
        Campus.objects.create(
            slug='ur-cst',
            name='UR-CST Reformed Bible Study',
            short_name='UR-CST',
            campus_type='University',
            image_alt='Students studying',
        )
        SiteEvent.objects.create(
            day='01',
            month='Aug',
            date_label='1 August',
            title='The Mission of the Church Conference',
            image_alt='Students at a conference',
        )
        ThursdaySession.objects.create(session='Session 1', time='11:00 AM – 1:00 PM')
        GalleryImage.objects.create(
            src='/images/gallery-01.webp',
            alt='Students together',
            title='After the gathering',
            category='Fellowship',
        )
        Testimonial.objects.create(quote='A place to grow.', name='A student', role='UR-CST')
        LeadershipTeam.objects.create(
            slug='oversight',
            title='Ministry oversight',
            summary='Guards the vision.',
            responsibilities=['Vision and direction'],
        )
        SiteArticle.objects.create(
            slug='three-ways-we-make-disciples',
            title='Three ways we make disciples',
            category='Discipleship',
            excerpt='How we pursue the mission.',
            image='/images/training-workshop.webp',
            image_alt='Students training together',
            sections=[{'heading': 'One', 'paragraphs': ['Teach the Word.']}],
        )
        FaithSection.objects.create(
            slug='the-bible',
            title='The Bible',
            paragraphs=['The Scriptures are inspired.'],
            scripture='2 Timothy 3:16',
        )

    def test_returns_every_collection_in_frontend_shape(self):
        response = self.client.get('/api/v1/site-content/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(
            set(data),
            {
                'site', 'nav', 'ministryExpressions', 'campuses', 'events',
                'thursdaySessions', 'gallery', 'testimonials',
                'leadershipTeams', 'articles', 'statementOfFaith',
            },
        )
        self.assertEqual(data['site']['shortName'], 'CSN')
        self.assertEqual(data['site']['joinPhone']['label'], '+250 784 857 707')
        self.assertEqual(data['site']['url'], 'https://christianstudentsnetwork.org')
        self.assertEqual(data['nav'][0]['label'], 'About')
        self.assertEqual(data['ministryExpressions'][0]['imageAlt'], 'Students in a small group')
        self.assertEqual(data['campuses'][0]['type'], 'University')
        self.assertEqual(data['events'][0]['dateLabel'], '1 August')
        self.assertEqual(data['gallery'][0]['src'], '/images/gallery-01.webp')
        self.assertEqual(data['articles'][0]['imageAlt'], 'Students training together')
        self.assertEqual(data['articles'][0]['sections'][0]['heading'], 'One')
        self.assertNotIn('scripture', data['articles'][0])
        self.assertEqual(data['statementOfFaith'][0]['slug'], 'the-bible')

    def test_empty_profile_still_returns_a_payload(self):
        SiteProfile.objects.all().delete()

        response = self.client.get('/api/v1/site-content/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['site']['name'], 'Christian Students Network')
