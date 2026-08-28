from django.db import models
from django.conf import settings


class SystemAuditLog(models.Model):
    ACTION_CHOICES = (
        ('USER_CREATE', 'User Created'),
        ('USER_UPDATE', 'User Updated'),
        ('ROLE_CHANGE', 'Role Changed'),
        ('STATUS_CHANGE', 'Account Status Changed'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('GROUP_CREATE', 'Group/Role Created'),
        ('GROUP_UPDATE', 'Group/Role Updated'),
        ('GROUP_DELETE', 'Group/Role Deleted'),
        ('SETTINGS_UPDATE', 'Platform Settings Updated'),
        ('MAINTENANCE_TOGGLE', 'Maintenance Mode Toggled'),
        ('SECURITY_EVENT', 'Security Event'),
        ('DATA_EXPORT', 'Data Exported'),
        ('ENTITY_DELETE', 'Entity Deleted'),
        ('OTHER', 'Other Administrative Action'),
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_audit_logs',
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default='OTHER', db_index=True)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Audit Log'
        verbose_name_plural = 'System Audit Logs'

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {actor_name} - {self.action}: {self.details[:60]}"
