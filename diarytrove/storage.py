from django.core.files.storage import FileSystemStorage
from django.conf import settings

class PrivateMediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(location=str(settings.PRIVATE_MEDIA_ROOT), base_url=None, *args, **kwargs)
