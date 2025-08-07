from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    username_email = forms.CharField(label=_("Username or email"), min_length=3, max_length=320, widget=forms.TextInput)
    password = forms.CharField(label=_("Password"), min_length=8, widget=forms.PasswordInput)
