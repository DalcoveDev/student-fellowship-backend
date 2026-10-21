import os

from django.core.exceptions import ValidationError
from django.db import models


def validate_file_extension(value):
    """Only allow safe document and image file types."""
    ALLOWED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.mp4', '.webm', '.mp3',
    }
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'File type "{ext}" is not allowed. '
            f'Allowed types: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
        )


def validate_file_size(value):
    """Reject files larger than 100 MB."""
    max_size = 100 * 1024 * 1024  # 100 MB
    if value.size > max_size:
        raise ValidationError(
            f'File size ({value.size / (1024 * 1024):.1f} MB) exceeds the 100 MB limit.'
        )


class MediaAsset(models.Model):
    file = models.FileField(
        upload_to='library/',
        validators=[validate_file_extension, validate_file_size],
    )
    title = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.file.name

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)
