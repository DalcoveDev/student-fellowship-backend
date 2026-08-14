from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('reader', 'Reader'),
        ('journalist', 'Journalist'),
        ('editor', 'Editor'),
        ('admin', 'Admin/Superadmin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reader')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    twitter = models.URLField(blank=True)
    github = models.URLField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserAuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performed_audit_logs')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='target_audit_logs')
    action = models.CharField(max_length=50)  # 'create', 'update', 'role_change', 'status_change', 'password_reset'
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"{actor_name} performed {self.action} on {self.target_user.username} at {self.timestamp}"

