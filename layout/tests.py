from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from layout.models import SiteSetting, MenuItem, DailyVerse, HomepageLayout, SocialLink, ContactInquiry
from articles.models import Category

User = get_user_model()


class LayoutTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            role='admin'
        )
        self.editor = User.objects.create_user(
            username='editoruser',
            email='editor@example.com',
            password='password123',
            role='editor'
        )

        self.site_setting = SiteSetting.objects.create(site_name='Test Site')

        self.category = Category.objects.create(name='Test Category', slug='test-category')

        self.menu_item_page = MenuItem.objects.create(title='Page', menu_type='page', page_slug='about')
        self.menu_item_category = MenuItem.objects.create(
            title='Category', menu_type='category', category=self.category)
        self.menu_item_article = MenuItem.objects.create(
            title='Article', menu_type='article', article_slug='test-article')
        self.menu_item_custom = MenuItem.objects.create(
            title='Custom', menu_type='custom', custom_url='https://example.com')

        self.today = timezone.now().date()
        self.daily_verse = DailyVerse.objects.create(
            date=self.today,
            verse_reference='John 1:1',
            verse_text_kinyarwanda='Mu ntangiriro Jambo yariho',
            verse_text_english='In the beginning was the Word'
        )

        self.layout_section = HomepageLayout.objects.create(
            page='home',
            section_type='hero',
            title='Main Hero',
            order=1
        )

        self.social_link = SocialLink.objects.create(
            platform='facebook',
            url='https://facebook.com/test'
        )

    def test_sitesetting_singleton_enforcement(self):
        with self.assertRaises(ValidationError):
            SiteSetting.objects.create(site_name='Another Site')

    def test_menuitem_target_url(self):
        self.assertEqual(self.menu_item_page.target_url, '/about')
        self.assertEqual(self.menu_item_category.target_url, '/c/test-category')
        self.assertEqual(self.menu_item_article.target_url, '/a/test-article')
        self.assertEqual(self.menu_item_custom.target_url, 'https://example.com')

    def test_dailyverse_unique_date(self):
        with self.assertRaises(Exception):
            DailyVerse.objects.create(
                date=self.today,
                verse_reference='John 1:2',
                verse_text_kinyarwanda='Test',
                verse_text_english='Test'
            )

    def test_public_homepage_layout(self):
        url = reverse('public-homepage-layout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_public_site_settings(self):
        url = reverse('site-settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['site_name'], 'Test Site')

    def test_public_daily_verse_today(self):
        url = reverse('daily-verse-today')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['verse_reference'], 'John 1:1')

    def test_public_social_links(self):
        url = reverse('public-social-links')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_public_menu(self):
        url = reverse('public-menus')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_contact_inquiry_submission(self):
        url = reverse('contact-inquiry')
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Hello',
            'message': 'Testing'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ContactInquiry.objects.filter(email='john@example.com').exists())

    def test_cms_layout_crud(self):
        list_url = reverse('cms-layout-list')
        detail_url = reverse('cms-layout-detail', args=[self.layout_section.id])

        self.client.force_authenticate(user=self.editor)

        # Read
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create
        data = {
            'page': 'home',
            'section_type': 'featured-grid',
            'title': 'Featured'
        }
        response = self.client.post(list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update
        update_data = {
            'page': 'home',
            'section_type': 'hero',
            'title': 'Updated Title'
        }
        response = self.client.put(detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cms_layout_sync_and_public_reflection(self):
        """Verify that updating section title, limit, and categories in CMS
        immediately syncs and reflects in public homepage layout API response."""
        cat2 = Category.objects.create(name='Sports News', slug='sports-news')
        detail_url = reverse('cms-layout-detail', args=[self.layout_section.id])
        public_url = reverse('public-homepage-layout')

        self.client.force_authenticate(user=self.editor)
        patch_data = {
            'title': 'Amakuru y’Ingenzi',
            'article_limit': 2,
            'category': self.category.id,
            'categories': [self.category.id, cat2.id]
        }
        response = self.client.patch(detail_url, patch_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Amakuru y’Ingenzi')
        self.assertEqual(response.data['article_limit'], 2)
        self.assertEqual(len(response.data['categories']), 2)

        # Public API call (unauthenticated)
        self.client.logout()
        pub_response = self.client.get(public_url)
        self.assertEqual(pub_response.status_code, status.HTTP_200_OK)
        hero_item = next((item for item in pub_response.data if item['section_type'] == 'hero'), None)
        self.assertIsNotNone(hero_item)
        self.assertEqual(hero_item['title'], 'Amakuru y’Ingenzi')
        self.assertEqual(hero_item['article_limit'], 2)
        self.assertEqual(hero_item['category_details']['name'], 'Test Category')
        self.assertEqual(len(hero_item['categories_details']), 2)

    def test_cms_settings_update(self):
        self.client.force_authenticate(user=self.editor)
        detail_url = reverse('cms-settings-detail', args=[self.site_setting.pk])

        update_data = {
            'site_name': 'Updated Site Name'
        }
        response = self.client.patch(detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cms_permissions(self):
        layout_url = reverse('cms-layout-list')

        # Anonymous
        response = self.client.get(layout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Reader
        reader = User.objects.create_user(username='reader', email='r@e.com', password='p', role='reader')
        self.client.force_authenticate(user=reader)
        response = self.client.get(layout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SiteInquiryApiTests(APITestCase):
    """The website's contact, join, and visit forms post here."""

    def setUp(self):
        # The view is throttled per IP; reset the throttle history per test.
        from django.core.cache import cache
        cache.clear()

    def test_contact_submission_is_saved(self):
        response = self.client.post('/api/v1/inquiries/', {
            'kind': 'contact',
            'name': 'Test Student',
            'email': 'test@example.com',
            'subject': 'General enquiry',
            'message': 'Hello from the website.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.kind, 'contact')
        self.assertEqual(inquiry.email, 'test@example.com')
        self.assertEqual(inquiry.message, 'Hello from the website.')

    def test_contact_requires_a_valid_email(self):
        response = self.client.post('/api/v1/inquiries/', {
            'kind': 'contact',
            'name': 'Test Student',
            'email': 'not-an-email',
            'subject': 'General enquiry',
            'message': 'Hello.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_join_requires_contact_details(self):
        response = self.client.post('/api/v1/inquiries/', {
            'kind': 'join',
            'name': 'Test Student',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('contact', response.data)

    def test_join_submission_defaults_subject_and_keeps_campus(self):
        response = self.client.post('/api/v1/inquiries/', {
            'kind': 'join',
            'name': 'Test Student',
            'contact': '+250 700 000 000',
            'campus': 'UR-CST Reformed Bible Study',
            'message': 'I would like to join.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.kind, 'join')
        self.assertEqual(inquiry.subject, 'Bible study enquiry')
        self.assertEqual(inquiry.campus, 'UR-CST Reformed Bible Study')

    def test_visit_submission_keeps_session(self):
        response = self.client.post('/api/v1/inquiries/', {
            'kind': 'visit',
            'name': 'Test Visitor',
            'contact': 'test@example.com',
            'campus': 'UR-CST',
            'session': 'Session 2',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.kind, 'visit')
        self.assertEqual(inquiry.session, 'Session 2')
        self.assertEqual(inquiry.subject, 'Visit plan')
