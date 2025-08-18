from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone

from .storage import PrivateMediaStorage

# Creating the private media storage object
private_storage = PrivateMediaStorage()


class Profile(models.Model):
    """
    Stores a user profile, with all its settings, data and preferences
    """
    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")
    
    EMAIL_MEMORIES = [(1, _("Always send")), (2, _("Only positive memories")), (3, _("Never send"))]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    editable_lock_time = models.BooleanField(_("Can the lock time be edited"), default=True)
    lock_time = models.IntegerField(_("Memories lock time in days"), default=365)
    mail_reminder = models.IntegerField(_("Email writing reminder delay in days"), default=7)
    last_memory_date = models.DateTimeField(_("Date of the last memory"), default=timezone.now)  # For reminder emails
    mail_memory = models.IntegerField(_("When to send memories by email"), choices=EMAIL_MEMORIES, default=1)
    mail_newsletter = models.BooleanField(_("Receive email newsletters"), default=True)

    def __str__(self):
        return str(_("%(user)s's profile") % {"user": self.user})


class Memory(models.Model):
    """
    Represents a memory entry and its attributes
    """
    class Meta:
        verbose_name = _("memory")
        verbose_name_plural = _("memories")
    
    MOODS = [(1, "😀"), (2, "🙂"), (3, "😊"), (4, "🤩"), (5, "😜"), (6, "😐"), (7, "😒"), (8, "😮‍💨"), (9, "😔"), (10, "🤕"), (11, "🙁"), (12, "😢")]
    POSITIVE_MOODS = (1, 2, 3, 4, 5)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Owner of the memory"))
    date = models.DateTimeField(_("Date of creation"), default=timezone.now)
    lock_time = models.IntegerField(_("Memory lock time in days"), default=0)  # Use 0 for the user preference
    title = models.CharField(_("Memory title"), max_length=255)
    content = models.TextField(_("Content of the memory"))
    mood = models.IntegerField(_("Mood for the memory"), choices=MOODS)
    mail_sent = models.BooleanField(_("Was it already sent"), default=False)

    def __str__(self):
        return f"{str(self.title)} ({self.pk})"


class MemoryMedia(models.Model):
    """
    Represents a private media uploaded by the user for a memory
    """
    class Meta:
        verbose_name = _("memory media")
        verbose_name_plural = _("memory media")
    
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, verbose_name=_("Memory of origin"))
    file = models.FileField(storage=private_storage, upload_to="memory_media")

    def __str__(self):
        return f"{self.file} ({self.pk})"
