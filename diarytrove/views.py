from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpRequest, HttpResponse, Http404, JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import Profile, Memory, MemoryMedia
from .forms import LoginForm, SignupForm, PreferencesForm
from .utils import regular_jobs, safe_join


def index(request:HttpRequest):
    """
    The page to return when requesting the index page
    """
    return render(request, "diarytrove/index.html", {"logged_in": request.user.is_authenticated})


def auth_signup(request:HttpRequest):
    """
    Page to create a new account, also handles POST data
    """
    if request.user.is_authenticated:
        return redirect("home")
    
    error_message = None
    if request.method == "POST":
        # Handle the signup data
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"].lower()  # emails are case insensitive
            password = form.cleaned_data["password"]
            password_confirm = form.cleaned_data["password_confirm"]

            # Check username validity and availability
            if not all(char.isalnum() or char in "._-+" for char in username):
                error_message = _("Username can only contain letters, numbers, and the following symbols: . _ - +")
            elif User.objects.filter(username=username).exists():
                error_message = _("This username is already taked, choose another one or use the log in page if you already created your account.")
            
            # Check email availability
            elif User.objects.filter(email=email).exists():
                error_message = _("This email address is already in use, use the log in page to log into your account instead.")

            # Check password matching and robustness
            elif password != password_confirm:
                error_message = _("The two passwords aren't matching. Make sure to type the same password twice.")
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    error_message = " ".join(e.messages)
                
                else:
                    # Register the user and log in
                    user = User.objects.create_user(username, email, password)
                    profile = Profile(user=user)
                    profile.save()
                    login(request, user)
                    return redirect("preferences")

        else:
            # Properly display the error for an invalid form
            error_message = "".join([error for errors in form.errors.values() for error in errors])
            form = SignupForm(initial=request.POST)
    
    else:
        # Create the form and give the page
        form = SignupForm()
    
    return render(request, "diarytrove/signup.html", {"form": form, "error":error_message})


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
                username_email = username_email.lower()  # emails are case insensitive
            
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
            # Properly display the error for an invalid form
            error_message = "".join([error for errors in form.errors.values() for error in errors])
            form = LoginForm(initial=request.POST)
    
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


def conditions(request:HttpRequest):
    """
    Returns  page with the terms and conditions
    """
    return render(request, "diarytrove/conditions.html", {"user": request.user})


def passwords(request:HttpRequest):
    """
    Returns a page explaining password security
    """
    return render(request, "diarytrove/passwords.html", {"user": request.user})


def contact_email(request:HttpRequest):
    """
    Redirects to a link to send an email
    """
    return HttpResponse(f"<script>window.location.href = 'mailto:{settings.CONTACT_EMAIL}';</script>")


@login_required
@regular_jobs
def preferences(request:HttpRequest):
    """
    Change the user preferences
    """
    error_message = None
    profile:Profile = request.user.profile
    if request.method == "POST":
        # Handle the submited preferences
        form = PreferencesForm(request.POST)
        if form.is_valid():
            editable_lock_time = form.cleaned_data["editable_lock_time"]
            lock_time = form.cleaned_data["lock_time"]
            mail_reminder = form.cleaned_data["mail_reminder"]
            mail_memory = form.cleaned_data["mail_memory"]
            mail_newsletter = form.cleaned_data["mail_newsletter"]

            if profile.editable_lock_time:
                profile.lock_time = lock_time

            # This cannot be enabled back
            if not editable_lock_time:
                profile.editable_lock_time = False
            
            try:
                mail_memory = int(mail_memory)
            except ValueError:
                error_message = _("The value for when to send memories by email is invalid, pick a valid option.")
            else:
                if not Profile.EMAIL_MEMORIES[0][0] <= mail_memory <= Profile.EMAIL_MEMORIES[-1][0]:
                    error_message = _("The value for when to send memories by email is invalid, pick a valid option.")
                else:
                    profile.mail_reminder = mail_reminder
                    profile.mail_newsletter = mail_newsletter
                    profile.save()
                    return redirect("home")
        
        else:
            # Properly display the error for an invalid form
            error_message = "".join([error for errors in form.errors.values() for error in errors])
            form = PreferencesForm(initial=request.POST)
    
    else:
        # Create the form and give the page
        form = PreferencesForm()
        form.fields["editable_lock_time"].initial = profile.editable_lock_time
        form.fields["lock_time"].initial = profile.lock_time
        form.fields["mail_reminder"].initial = profile.mail_reminder
        form.fields["mail_memory"].initial = profile.mail_memory
        form.fields["mail_newsletter"].initial = profile.mail_newsletter
    
    return render(request, "diarytrove/preferences.html", {"form": form, "error":error_message, "editable":profile.editable_lock_time})


@login_required(redirect_field_name=None, login_url="index")  # Simply redirect to the index if the user is not logged in
@regular_jobs
def home(request:HttpRequest):
    """
    The user's home page
    """
    user = request.user

    return render(request, "diarytrove/home.html", {"user": user})


@login_required
@regular_jobs
def memory_create(request:HttpRequest):
    """
    View to create a new memory
    """
    profile:Profile = request.user.profile
    limit_mib = round(settings.MAX_SUBMIT_MEDIA_SIZE / 2**20, 3)

    if request.method == "POST":
        # Handle posted data
        if not all([elem in request.POST and request.POST.get(elem, "") != "" for elem in ("title", "content", "mood", "lock_time")]):
            return JsonResponse({"success": False, "error": _("Some required fields are missing.")}, status=400)
        
        title = request.POST["title"]
        content = request.POST["content"]
        lock_time = request.POST["lock_time"]
        mood = request.POST["mood"]
        
        # Validate the data
        if not title or not content:
            return JsonResponse({"success": False, "error": _("Title and content cannot be empty.")}, status=400)
        if not profile.editable_lock_time:
            lock_time = 0  # Don't allow lock time modification if it's specified in the preferences
        else:
            try:
                lock_time = int(lock_time)
            except ValueError:
                return JsonResponse({"success": False, "error": _("Lock time must be a valid integer.")}, status=400)
            if lock_time < 0:
                return JsonResponse({"success": False, "error": _("Lock time cannot be negative.")}, status=400)
        try:
            mood = int(mood)
        except ValueError:
            return JsonResponse({"success": False, "error": _("Please select a valid mood.")}, status=400)
        if not Memory.MOODS[0][0] <= mood <= Memory.MOODS[-1][0]:
            return JsonResponse({"success": False, "error": _("Please select a valid mood.")}, status=400)
        
        # Validate uploaded files
        files = request.FILES.getlist("files[]")
        total_size = 0  # Files size in bytes

        for f in files:
            try:
                total_size += f.size
            except Exception:
                return JsonResponse({"success": False, "error": _("Unable to calculat file size.")}, status=400)

        if total_size > settings.MAX_SUBMIT_MEDIA_SIZE:
            # The uploaded files are too large
            total_size_mib = round(total_size / 2**20, 3)
            return JsonResponse({"success": False,
                                 "error": _("The uploaded files are too large. The maximum is %(limit)s MiB total, you uploaded %(size)s Mib.") % {"limit": limit_mib, "size": total_size_mib}},
                                status=400)

        # Create the memory object
        raise Http404()
        memory = Memory(owner=request.user, date=timezone.now(), lock_time=lock_time,
                        title=title, content=content, mood=mood)
        memory.save()

        for f in files:
            MemoryMedia.objects.create(memory=memory, file=f)

        # Return json for AJAX requests or redirect for normal requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "redirect": reverse("memory_view", args=[memory.pk])})
        return redirect("memory_view", memory.pk, {"profile": profile})

    # Give the page for GET requests
    return render(request, "diarytrove/memory_create.html", {"profile": request.user.profile,
                                                             "moods": [mood[1] for mood in Memory.MOODS],
                                                             "max_upload_bytes": settings.MAX_SUBMIT_MEDIA_SIZE,
                                                             "max_upload_mib": limit_mib})


@login_required
@regular_jobs
def memory_view(request:HttpRequest, memory_pk:int):
    """
    View to display a memory
    """
    return HttpResponse("NOT IMPLEMENTED")  #TODO
