from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    username_email = forms.CharField(label=_("Username or email"), min_length=3, max_length=320)
    password = forms.CharField(label=_("Password"), min_length=8, widget=forms.PasswordInput)


class SignupForm(forms.Form):
    username = forms.CharField(label=_("Username"), min_length=3, max_length=64)
    email = forms.EmailField(label=_("Email address"), min_length=4, max_length=320)
    password = forms.CharField(label=_("Password"), min_length=8, widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=_("Confirm password"), min_length=8, widget=forms.PasswordInput)


class PreferencesForm(forms.Form):
    editable_lock_time = forms.BooleanField(label=_("Can the lock time be edited"), required=False)
    lock_time = forms.IntegerField(label=_("Memories lock time in days"), min_value=1, required=False)
    mail_reminder = forms.IntegerField(label=_("Email writing reminder delay in days"), min_value=1)
    mail_memory = forms.ChoiceField(label=_("When to send memories by email"),
                                    choices=[(1, _("Always send")), (2, _("Only positive memories")), (3, _("Never send"))],
                                    widget=forms.Select)
    mail_newsletter = forms.BooleanField(label=_("Receive email newsletters"), required=False)
