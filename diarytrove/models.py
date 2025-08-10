from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User
from django.conf import settings

import datetime


class Profile(models.Model):
    """
    a model to store a user profile, with all its settings, data and preferences
    """
    EMAIL_MEMORIES = [(1, _("Always send")), (2, _("Only positive memories")), (3, _("Never send"))]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    editable_lock_time = models.BooleanField(_("can the lock time be edited"), default=True)
    lock_time = models.DurationField(_("memories lock time"), default=datetime.timedelta(days=365))
    mail_reminder = models.DurationField(_("email writing reminder delay"), default=datetime.timedelta(days=7))
    mail_memory = models.IntegerField(_("when to send memories by email"), choices=EMAIL_MEMORIES, default=1)
    mail_newsletter = models.BooleanField(_("receive email newsletters"), default=True)

    def __str__(self):
        return str(_("%(user)s's profile") % {"user": self.user})