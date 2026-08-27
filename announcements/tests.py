from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Announcement

User = get_user_model()


class AnnouncementModelTest(TestCase):
    def test_announcement_creation(self):
        announcement = Announcement.objects.create(
            title='Test Announcement',
            body='This is a test.',
            announcement_type='akazi',
            organization_name='Test Org',
            reference_number='REF-123'
        )
        self.assertEqual(announcement.title, 'Test Announcement')
        self.assertEqual(announcement.announcement_type, 'akazi')

    def test_type_choices_validation(self):
        announcement = Announcement(
            title='Invalid Type',
            body='Test',
            announcement_type='invalid_type',
            organization_name='Test Org'
        )
        # full_clean checks choices
        with self.assertRaises(ValidationError):
            announcement.full_clean()


class AnnouncementAPITest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password',
            role='admin'
        )
        self.reader_user = User.objects.create_user(
            username='reader',
            email='reader@test.com',
            password='password',
            role='reader'
        )
        self.announcement = Announcement.objects.create(
            title='Public Announcement',
            body='Body of announcement',
            announcement_type='amasoko',
            organization_name='Org',
            is_active=True
        )
        self.public_list_url = reverse('public-announcement-list')
        self.public_detail_url = reverse('public-announcement-detail', kwargs={'pk': self.announcement.pk})
        self.cms_list_url = reverse('cms-announcements-list')

    def test_public_api_list(self):
        response = self.client.get(self.public_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if list or paginated response
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['title'], 'Public Announcement')

    def test_public_api_detail(self):
        response = self.client.get(self.public_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Public Announcement')

    def test_cms_api_create_and_permissions(self):
        # Admin can create
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.cms_list_url, {
            'title': 'CMS Announcement',
            'body': 'Body content',
            'announcement_type': 'akazi',
            'organization_name': 'New Org'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Announcement.objects.count(), 2)

        # Reader denied
        self.client.force_authenticate(user=self.reader_user)
        response = self.client.post(self.cms_list_url, {
            'title': 'Hacked',
            'body': 'Hacked',
            'announcement_type': 'akazi',
            'organization_name': 'Hacker Org'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
