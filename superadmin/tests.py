from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from layout.models import SiteSetting
from superadmin.models import SystemAuditLog

User = get_user_model()


class SuperAdminTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.superadmin = User.objects.create_superuser(
            username='admin_boss',
            email='admin@isezerano.rw',
            password='superadminpass123',
            role='admin',
        )

        self.editor = User.objects.create_user(
            username='editor_ed',
            email='editor@isezerano.rw',
            password='editorpass123',
            role='editor',
            is_staff=True,
        )

        self.journalist = User.objects.create_user(
            username='journo_joe',
            email='joe@isezerano.rw',
            password='journopass123',
            role='journalist',
            is_staff=True,
        )

        self.reader = User.objects.create_user(
            username='reader_alice',
            email='alice@isezerano.rw',
            password='readerpass123',
            role='reader',
            is_staff=False,
        )

        self.setting = SiteSetting.objects.create(
            site_name="Isezerano News",
            maintenance_mode=False,
        )

    def test_unauthenticated_access_denied(self):
        url = reverse('superadmin-stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_reader_access_denied(self):
        self.client.force_authenticate(user=self.reader)
        url = reverse('superadmin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_journalist_access_denied(self):
        self.client.force_authenticate(user=self.journalist)
        url = reverse('superadmin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_access_denied(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse('superadmin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superadmin_stats_view_success(self):
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('superadmin-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        self.assertIn('user_roles', response.data)
        self.assertEqual(response.data['overview']['total_users'], 4)

    def test_superadmin_create_user(self):
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('superadmin-users-list')
        payload = {
            'username': 'new_staff_member',
            'email': 'staff@isezerano.rw',
            'password': 'SecureStaffPassword123!',
            'role': 'journalist',
            'first_name': 'Jean',
            'last_name': 'Dupont',
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='new_staff_member').exists())
        created_user = User.objects.get(username='new_staff_member')
        self.assertTrue(created_user.is_staff)
        self.assertTrue(
            SystemAuditLog.objects.filter(action='USER_CREATE', target_id=str(created_user.id)).exists()
        )

    def test_superadmin_update_user_role(self):
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('superadmin-users-detail', kwargs={'pk': self.reader.pk})
        payload = {'role': 'journalist'}
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reader.refresh_from_db()
        self.assertEqual(self.reader.role, 'journalist')
        self.assertTrue(self.reader.is_staff)

    def test_superadmin_toggle_user_status(self):
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('superadmin-users-toggle-active', kwargs={'pk': self.reader.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reader.refresh_from_db()
        self.assertFalse(self.reader.is_active)

    def test_superadmin_reset_user_password(self):
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('superadmin-users-reset-password', kwargs={'pk': self.reader.pk})
        payload = {'password': 'BrandNewPassword2026!'}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reader.refresh_from_db()
        self.assertTrue(self.reader.check_password('BrandNewPassword2026!'))

    def test_superadmin_create_and_manage_group(self):
        self.client.force_authenticate(user=self.superadmin)
        perm = Permission.objects.first()
        url = reverse('superadmin-groups-list')
        payload = {
            'name': 'Editorial Leads',
            'permission_ids': [perm.id] if perm else [],
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Group.objects.filter(name='Editorial Leads').exists())

    def test_superadmin_update_settings_and_toggle_maintenance(self):
        self.client.force_authenticate(user=self.superadmin)
        toggle_url = reverse('superadmin-toggle-maintenance')
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.setting.refresh_from_db()
        self.assertTrue(self.setting.maintenance_mode)

    def test_superadmin_list_audit_logs(self):
        SystemAuditLog.objects.create(
            actor=self.superadmin,
            action='SECURITY_EVENT',
            details='Test audit log message',
            ip_address='127.0.0.1',
        )
        self.client.force_authenticate(user=self.superadmin)
        url = reverse('superadmin-logs-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
