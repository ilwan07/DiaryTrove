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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    receive_newsletters = models.BooleanField(_("receive the newsletters"), default=True)

    def __str__(self):
        return str(_("%(user)s's profile") % {"user": self.user})