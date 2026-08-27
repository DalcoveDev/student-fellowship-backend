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
        self.menu_item_category = MenuItem.objects.create(title='Category', menu_type='category', category=self.category)
        self.menu_item_article = MenuItem.objects.create(title='Article', menu_type='article', article_slug='test-article')
        self.menu_item_custom = MenuItem.objects.create(title='Custom', menu_type='custom', custom_url='https://example.com')
        
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
