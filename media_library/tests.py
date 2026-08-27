import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import MediaAsset, validate_file_extension, validate_file_size

User = get_user_model()


class MediaAssetModelTest(TestCase):
    def test_file_extension_validation(self):
        # Allowed extension
        allowed_file = SimpleUploadedFile(
            'test.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 10,
            content_type='image/png'
        )
        # Should not raise exception
        validate_file_extension(allowed_file)

        # Blocked extension
        blocked_file = SimpleUploadedFile(
            'test.exe',
            b'MZ',
            content_type='application/x-msdownload'
        )
        with self.assertRaises(ValidationError):
            validate_file_extension(blocked_file)

    def test_file_size_validation(self):
        small_file = SimpleUploadedFile('small.png', b'a' * 10)
        validate_file_size(small_file)

        # Mock size attribute since creating a 11MB file in memory is slow
        large_file = SimpleUploadedFile('large.png', b'a')
        large_file.size = 11 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_file_size(large_file)

    def test_auto_title_from_filename(self):
        f = SimpleUploadedFile(
            'my_test_image.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 10,
            content_type='image/png'
        )
        asset = MediaAsset(file=f)
        asset.save()
        self.assertEqual(asset.title, 'my_test_image.png')


class MediaAssetAPITest(APITestCase):
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
        self.list_url = reverse('cms-media-list')

    def test_upload_media_asset_and_list(self):
        self.client.force_authenticate(user=self.admin_user)
        image = SimpleUploadedFile(
            'test.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            content_type='image/png'
        )
        
        response = self.client.post(self.list_url, {
            'file': image,
            'caption': 'A test image'
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MediaAsset.objects.count(), 1)
        self.assertEqual(MediaAsset.objects.first().caption, 'A test image')
        
        # Test List
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permissions(self):
        # Reader should be denied
        self.client.force_authenticate(user=self.reader_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Anonymous should be denied
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
