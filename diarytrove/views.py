from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpRequest, HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Profile
from .forms import LoginForm

import datetime


def index(request:HttpRequest):
    """
    The page to return when requesting the index page
    """
    return render(request, "diarytrove/index.html", {"logged_in": request.user.is_authenticated})


def auth_signup(request:HttpRequest):
    """
    Page to create a new account, also handles POST data
    """
    return HttpResponse("NOT IMPLEMENTED")


def auth_login(request:HttpRequest):
    """
    Page to log into an existing account
    """
    if request.method == "POST":
        # Handle the login data
        form = LoginForm(request.POST)
        if form.is_valid():
            pass  #TODO: hande login data
    
    else:
        # Create the form and give the page
        form = LoginForm()
    
    return render(request, "diarytrove/login.html", {"form": form})


def auth_logout(request:HttpRequest):
    """
    Logs out the current user
    """
    logout(request)
    return redirect("index")


@login_required
def home(request:HttpRequest):
    """
    The user's home page
    """
    return HttpResponse("NOT IMPLEMENTED")
