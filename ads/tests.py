from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import AdSlot

User = get_user_model()


class AdsModelTests(TestCase):
    def test_ctr_calculation_zero_impressions(self):
        now = timezone.now()
        ad = AdSlot.objects.create(
            name='Test', placement='header_banner',
            start_date=now, end_date=now + timedelta(days=1),
            impressions=0, clicks=5
        )
        self.assertEqual(ad.ctr, 0.0)

    def test_ctr_calculation(self):
        now = timezone.now()
        ad = AdSlot.objects.create(
            name='Test', placement='header_banner',
            start_date=now, end_date=now + timedelta(days=1),
            impressions=1000, clicks=25
        )
        self.assertEqual(ad.ctr, 2.5)


class AdsAPITests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin', email='a@a.com', password='pw', role='admin')
        self.editor = User.objects.create_user(username='editor', email='e@a.com', password='pw', role='editor')
        self.reader = User.objects.create_user(username='reader', email='r@a.com', password='pw', role='reader')

        now = timezone.now()
        self.ad = AdSlot.objects.create(
            name='Banner 1',
            placement='header_banner',
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
            is_active=True,
            priority=10
        )
        self.inactive_ad = AdSlot.objects.create(
            name='Banner 2',
            placement='sidebar-rail',
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7),
            is_active=False
        )

    def test_active_ad_public_success(self):
        url = reverse('active-ad', kwargs={'placement': 'header_banner'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Banner 1')

    def test_active_ad_public_normalise_placement(self):
        url = reverse('active-ad', kwargs={'placement': 'header-banner'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Banner 1')

    def test_active_ad_public_not_found(self):
        url = reverse('active-ad', kwargs={'placement': 'sidebar-rail'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_track_analytics(self):
        url = reverse('track-analytics')
        data = {
            'event_type': 'ad_impression',
            'ad_slot': self.ad.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.impressions, 1)

    def test_cms_list_ads_permission_denied(self):
        self.client.force_authenticate(user=self.reader)
        url = reverse('cms-ads-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cms_create_ad_editor(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse('cms-ads-list')
        now = timezone.now()
        data = {
            'name': 'New Ad',
            'placement': 'sports_sidebar',
            'start_date': now.isoformat(),
            'end_date': (now + timedelta(days=5)).isoformat(),
            'is_active': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AdSlot.objects.count(), 3)
