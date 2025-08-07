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
    if request.user.is_authenticated:
        return redirect("home")
    
    error_message = None
    if request.method == "POST":
        # Handle the login data
        form = LoginForm(request.POST)
        if form.is_valid():
            username_email = form.cleaned_data["username_email"]
            password = form.cleaned_data["password"]

            login_type = "email" if "@" in username_email else "username"
            if login_type == "email":
                username_email = username_email.lower()  # emails are case insensitive, so standarize everything to lowercase
            
            # Check the validity of the credentials
            try:
                if login_type == "username":
                    user_object = User.objects.get(username=username_email)
                else:
                    user_object = User.objects.get(email=username_email)
            except User.DoesNotExist:
                error_message = _("This username/email isn't registered, sign up for a new account if you don't already have one.")
            except User.MultipleObjectsReturned:
                error_message = _("Multiple users are using this email, please use your username instead.")

            else:
                # Verify the password
                username = user_object.username
                user = authenticate(request, username=username, password=password)
                if user is None:
                    error_message = _("The entered password is wrong, try again.")
                else:
                    # Log the user in then redirect
                    login(request, user)
                    if "next" in request.POST:
                        return redirect(request.POST["next"])
                    else:
                        return redirect("home")
    
    else:
        # Create the form and give the page
        form = LoginForm()
    
    return render(request, "diarytrove/login.html", {"form": form, "error":error_message})


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
