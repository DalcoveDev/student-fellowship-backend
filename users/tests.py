from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import UserAuditLog

User = get_user_model()

class UserManagementTests(APITestCase):
    def setUp(self):
        # Create different operator users
        self.admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='testpassword',
            role='admin'
        )
        self.editor = User.objects.create_user(
            username='editor_test',
            email='editor@test.com',
            password='testpassword',
            role='editor'
        )
        self.reader = User.objects.create_user(
            username='reader_test',
            email='reader@test.com',
            password='testpassword',
            role='reader'
        )
        
        # Test targets
        self.target_user = User.objects.create_user(
            username='target_user',
            email='target@test.com',
            password='testpassword',
            role='reader'
        )

        self.list_url = reverse('cms-users-list')
        self.detail_url = reverse('cms-users-detail', kwargs={'pk': self.target_user.pk})
        self.reset_password_url = reverse('cms-users-reset-password', kwargs={'pk': self.target_user.pk})
        self.audit_log_list_url = reverse('cms-user-audit-logs-list')

    def test_unauthorized_user_management_access(self):
        # 1. Anonymous access
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Reader access
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Editor access
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all users
        self.assertGreaterEqual(len(response.data.get('results', []) if isinstance(response.data, dict) else response.data), 4)

    def test_admin_create_user_success(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'username': 'new_journalist',
            'email': 'journalist@test.com',
            'password': 'securepass123',
            'role': 'journalist',
            'first_name': 'New',
            'last_name': 'Journalist',
            'is_active': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user created and password hashed
        new_user = User.objects.get(username='new_journalist')
        self.assertTrue(new_user.check_password('securepass123'))
        self.assertEqual(new_user.role, 'journalist')
        self.assertTrue(new_user.is_staff)  # Journalist role should auto-align is_staff

        # Verify audit log recorded
        audit_log = UserAuditLog.objects.filter(target_user=new_user).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'create')
        self.assertEqual(audit_log.actor, self.admin)
        self.assertIn("Created user new_journalist", audit_log.details)

    def test_create_user_validation(self):
        self.client.force_authenticate(user=self.admin)
        
        # 1. Test duplicate username
        data = {
            'username': 'target_user',
            'email': 'different_email@test.com',
            'password': 'securepass123',
            'role': 'editor'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

        # 2. Test duplicate email (case-insensitive check)
        data = {
            'username': 'unique_username',
            'email': 'TARGET@TEST.COM',
            'password': 'securepass123',
            'role': 'editor'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_admin_update_user(self):
        self.client.force_authenticate(user=self.admin)
        
        # Update role to editor and bio
        data = {
            'role': 'editor',
            'bio': 'An experienced editor.',
            'username': 'target_user',
            'email': 'target@test.com'
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, 'editor')
        self.assertTrue(self.target_user.is_staff)
        self.assertEqual(self.target_user.bio, 'An experienced editor.')

        # Verify audit log
        audit_log = UserAuditLog.objects.filter(target_user=self.target_user, action='role_change').first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.actor, self.admin)
        self.assertIn("Changed role from reader to editor", audit_log.details)

    def test_admin_deactivate_user(self):
        self.client.force_authenticate(user=self.admin)
        
        data = {'is_active': False}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

        # Verify audit log
        audit_log = UserAuditLog.objects.filter(target_user=self.target_user, action='status_change').first()
        self.assertIsNotNone(audit_log)
        self.assertIn("Account deactivated", audit_log.details)

    def test_admin_reset_password(self):
        self.client.force_authenticate(user=self.admin)
        
        data = {'password': 'brandnewpassword123'}
        response = self.client.post(self.reset_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password('brandnewpassword123'))

        # Verify audit log
        audit_log = UserAuditLog.objects.filter(target_user=self.target_user, action='password_reset').first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.actor, self.admin)

    def test_audit_logs_permissions(self):
        # 1. Non-admin editor check
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(self.audit_log_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin check
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.audit_log_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
