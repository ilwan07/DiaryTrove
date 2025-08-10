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
    pass