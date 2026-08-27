from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from newsletter.models import Subscriber, NewsletterCampaign

User = get_user_model()


class NewsletterTests(APITestCase):
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
        self.reader = User.objects.create_user(
            username='readeruser',
            email='reader@example.com',
            password='password123',
            role='reader'
        )

        self.subscriber = Subscriber.objects.create(email='test@example.com')
        self.campaign = NewsletterCampaign.objects.create(
            subject='Test Campaign',
            body='<h1>Hello</h1>'
        )

    def test_subscriber_creation(self):
        subscriber = Subscriber.objects.create(email='new@example.com')
        self.assertEqual(subscriber.email, 'new@example.com')
        self.assertTrue(subscriber.is_active)

    def test_duplicate_email_subscriber(self):
        with self.assertRaises(IntegrityError):
            Subscriber.objects.create(email='test@example.com')

    def test_subscribe_endpoint(self):
        url = reverse('newsletter-subscribe')
        data = {'email': 'api@example.com'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Subscriber.objects.filter(email='api@example.com').exists())

    def test_cms_subscriber_list_permissions(self):
        url = reverse('cms-subscribers-list')

        # Anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Reader
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Editor
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_cms_campaign_crud(self):
        list_url = reverse('cms-campaigns-list')
        detail_url = reverse('cms-campaigns-detail', args=[self.campaign.id])

        # Admin required for campaigns
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(list_url)
        # Assuming IsAdmin permission on CMSNewsletterCampaignViewSet
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)

        # Read
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create
        data = {'subject': 'New Campaign', 'body': 'Content'}
        response = self.client.post(list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update
        update_data = {'subject': 'Updated Campaign', 'body': 'Content'}
        response = self.client.put(detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
