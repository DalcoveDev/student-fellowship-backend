"""Storage backend: Cloudinary with automatic local filesystem fallback."""
import logging

from django.core.files.storage import FileSystemStorage
from cloudinary_storage.storage import MediaCloudinaryStorage

logger = logging.getLogger(__name__)


class ResilientCloudinaryStorage(MediaCloudinaryStorage):
    """
    Try Cloudinary first. If the account/key rejects uploads
    (missing create permission, network, etc.), save locally instead
    so CMS uploads keep working.

    When a file exists on local disk (fallback uploads), serve its
    /media/ URL instead of a broken Cloudinary URL.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fs = FileSystemStorage()

    def _save(self, name, content):
        try:
            return super()._save(name, content)
        except Exception as exc:
            logger.warning(
                "Cloudinary upload failed (%s); falling back to local MEDIA_ROOT storage.",
                exc,
            )
            # Rewind file pointer if possible before local save
            if hasattr(content, 'seek'):
                try:
                    content.seek(0)
                except Exception:
                    pass
            return self._fs._save(name, content)

    def url(self, name):
        # Prefer local file URL when fallback saved the asset on disk
        if name and not str(name).startswith(('http://', 'https://')) and self._fs.exists(name):
            return self._fs.url(name)
        return super().url(name)

    def exists(self, name):
        if name and self._fs.exists(name):
            return True
        try:
            return super().exists(name)
        except Exception:
            return False

    def _open(self, name, mode='rb'):
        if name and self._fs.exists(name):
            return self._fs._open(name, mode)
        return super()._open(name, mode)
