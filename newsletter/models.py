from django.db import models

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Unsubscribed'})"

class NewsletterCampaign(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
    )

    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="HTML email content")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
