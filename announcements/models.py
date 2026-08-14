from django.db import models
from django.utils import timezone

class Announcement(models.Model):
    ANNOUNCEMENT_TYPES = (
        ('amasoko', 'Amasoko (Tenders)'),
        ('ibyemezo_by_urukiko', "Ibyemezo by'Urukiko (Court Decisions)"),
        ('akazi', 'Akazi (Jobs)'),
        ('guhindura_amazina', 'Guhindura Amazina (Name Change)'),
        ('other', 'Other'),
    )

    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Full announcement description or content")
    announcement_type = models.CharField(max_length=30, choices=ANNOUNCEMENT_TYPES)
    organization_name = models.CharField(max_length=255, help_text="e.g. QATAR CHARITY RWANDA, BPR Bank Rwanda Plc")
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    published_date = models.DateField(default=timezone.now)
    deadline_date = models.DateField(blank=True, null=True, help_text="Application or submission deadline")
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True, help_text="Optional PDF attachment")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published_date', '-id']
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"

    def __str__(self):
        return f"[{self.get_announcement_type_display()}] {self.title} - {self.organization_name}"
