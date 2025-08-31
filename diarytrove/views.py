from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpRequest, HttpResponse, Http404, JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone, translation
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import Profile, Memory, MemoryMedia
from .forms import LoginForm, SignupForm, PreferencesForm
from .utils import needs_profile, memory_media_mimetype, private_media_response, memory_to_dict, send_email

from pathlib import Path
import random
import os


def index(request:HttpRequest):
    """
    The page to return when requesting the index page
    """
    return render(request, "diarytrove/index.html", {"user": request.user})


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
                    # Get the preferred language
                    language = request.POST.get("language", "en")
                    if language not in [lang[0] for lang in Profile.AVAILABLE_LANGUAGES]:
                        language = "en"
                    
                    # Register the user and log in
                    user = User.objects.create_user(username, email, password)
                    profile = Profile(user=user, language=language)
                    profile.save()
                    login(request, user)
                    with translation.override(language):
                        send_email(user, "welcome", _("Welcome to DiaryTrove!"))
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
                    if "next" in request.POST and request.POST.get("next", "").startswith("/"):  # Only redirect on this site
                        return redirect(request.POST.get("next", "home"))
                    else:
                        return redirect("home")
        
        else:
            # Properly display the error for an invalid form
            error_message = "".join([error for errors in form.errors.values() for error in errors])
            form = LoginForm(initial=request.POST)
    
    else:
        # Create the form and give the page
        form = LoginForm()
    
    next_url = request.GET["next"] if "next" in request.GET else request.POST["next"] if "next" in request.POST else None
    return render(request, "diarytrove/login.html", {"form": form, "error": error_message, "next": next_url})


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
    return render(request, "diarytrove/information/conditions.html", {"user": request.user})


def passwords(request:HttpRequest):
    """
    Returns a page explaining password security
    """
    return render(request, "diarytrove/information/passwords.html", {"user": request.user})


def contact_email(request:HttpRequest):
    """
    Redirects to a link to send an email
    """
    return HttpResponse(f"<script>window.location.href = 'mailto:{settings.CONTACT_EMAIL}';</script>")


@login_required
@needs_profile
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
            language = form.cleaned_data["language"]

            if profile.editable_lock_time:
                profile.lock_time = lock_time

            # This cannot be enabled back
            if not editable_lock_time:
                profile.editable_lock_time = False
            
            profile.mail_reminder = mail_reminder
            profile.mail_memory = int(mail_memory)
            profile.language = language
            profile.mail_newsletter = mail_newsletter
            profile.save()
            error_message = _("Preferences saved successfully!")
        
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
        form.fields["language"].initial = profile.language
        form.fields["mail_newsletter"].initial = profile.mail_newsletter
    
    return render(request, "diarytrove/preferences.html", {"form": form, "error":error_message, "editable":profile.editable_lock_time})


@login_required(redirect_field_name=None, login_url="index")  # Simply redirect to the index if the user is not logged in
@needs_profile
def home(request:HttpRequest):
    """
    The user's home page
    """
    user = request.user
    latest_memory, random_memory = None, None
    unlocked_memories = [memory for memory in user.memory_set.all().order_by("-date") if memory.is_unlocked()]
    
    if len(unlocked_memories) >= 1:
        latest_memory = memory_to_dict(unlocked_memories.pop(0))
    if len(unlocked_memories) >= 1:  # If there's still a memory left
        random_memory = memory_to_dict(random.choice(unlocked_memories))

    return render(request, "diarytrove/home.html",
                  {"user": user, "latest_memory": latest_memory, "random_memory": random_memory})


@login_required
def gallery(request:HttpRequest):
    """
    A gallery to browse unlocked memories
    """
    all_memories = request.user.memory_set.all().order_by("-date")
    if "s" in request.GET:
        query = request.GET.get("s", "").strip().lower()
        wanted_memories = []
        for memory in all_memories:
            if query in str(memory.title).lower() or query in str(memory.content).lower():
                wanted_memories.append(memory)
    else:
        wanted_memories = all_memories
    
    memories = []
    for memory in wanted_memories:
        if memory.is_unlocked():
            memories.append(memory_to_dict(memory))
    
    return render(request, "diarytrove/gallery.html",  {"memories": memories})


@login_required
@needs_profile
def memory_create(request:HttpRequest):
    """
    View to create a new memory
    """
    profile:Profile = request.user.profile
    limit_bytes = settings.MAX_SUBMIT_MEDIA_SIZE
    limit_mib = round(limit_bytes / 2**20, 3)
    
    # Check if the media storage is full
    if not os.path.exists(settings.PRIVATE_MEDIA_ROOT):
        storage_full = True  # Consider the storage full if it doesn't exist
    else:
        total_disk_max = settings.MAX_GLOBAL_MEDIA_SIZE
        total_disk_used = os.path.getsize(settings.PRIVATE_MEDIA_ROOT)
        storage_full = total_disk_used >= total_disk_max - limit_bytes  # The space should be enough for any new memory

    if request.method == "POST":
        # Handle post data
        if not all([elem in request.POST and request.POST.get(elem, "") != "" for elem in ("title", "content", "mood", "lock_time")]):
            return JsonResponse({"success": False, "error": _("Some required fields are missing.")}, status=400)
        
        title = request.POST["title"]
        content = request.POST["content"]
        lock_time = request.POST["lock_time"]
        mood = request.POST["mood"]
        
        # Validate the data
        if not title or not content:
            return JsonResponse({"success": False, "error": _("Title and content cannot be empty.")}, status=400)
        if len(str(title)) > 255:
            return JsonResponse({"success": False, "error": _("Title cannot be longer than 255 characters.")}, status=400)
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
        if storage_full and files:
            return JsonResponse({"success": False, "error": _("The media storage is full, you cannot upload new files.")}, status=400)
        
        total_size = 0  # Files size in bytes

        for f in files:
            try:
                total_size += f.size
            except Exception:
                return JsonResponse({"success": False, "error": _("Unable to calculat file size.")}, status=400)

        if total_size > limit_bytes:
            # The uploaded files are too large
            total_size_mib = round(total_size / 2**20, 3)
            return JsonResponse({"success": False,
                                 "error": _("The uploaded files are too large. The maximum is %(limit)s MiB total, you uploaded %(size)s Mib.") % {"limit": limit_mib, "size": total_size_mib}},
                                status=400)

        # Create the memory object
        memory = Memory(owner=request.user, lock_time=lock_time, title=str(title).strip(), content=str(content).strip(), mood=mood)
        memory.save()

        # Update the last memory creation date
        profile.last_memory_date = timezone.now()
        profile.sent_writing_reminder = False
        profile.save()

        for f in files:
            MemoryMedia.objects.create(memory=memory, file=f)

        # Return json for AJAX requests or redirect for normal requests
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "redirect": reverse("home")})
        return redirect("home")

    # Give the page for GET requests
    return render(request, "diarytrove/memory_create.html", {"profile": request.user.profile,
                                                             "moods": [mood[1] for mood in Memory.MOODS],
                                                             "max_upload_bytes": limit_bytes,
                                                             "max_upload_mib": limit_mib,
                                                             "storage_full": storage_full})


@login_required
def memory_view(request:HttpRequest, memory_pk:int):
    """
    View to display a memory
    """
    user = request.user
    memory:Memory = get_object_or_404(Memory, pk=memory_pk)


    owner = memory.owner
    owner_profile:Profile = owner.profile

    # Verify access rights
    if not (user.is_superuser or user == owner):
        raise PermissionDenied("You are not the owner of this memory")
    
    # Check if the memory is unlocked
    lock_time = memory.lock_time
    if lock_time == 0:
        lock_time = owner_profile.lock_time
    
    if memory.date + timezone.timedelta(days=lock_time) >= timezone.now():
        raise Http404("This memory is still locked")
    
    # Create a list of the memory media objects with the media primary keys, the rough media types and the mimetypes
    media_data = []
    for memory_media in memory.memorymedia_set.all():
        ctype = memory_media_mimetype(memory_media)
        if ctype.startswith("image/"):
            media_type = "image"
        elif ctype.startswith("video/"):
            media_type = "video"
        elif ctype.startswith("audio/"):
            media_type = "audio"
        else:
            media_type = "file"
        media_data.append({"pk": memory_media.pk, "filename": Path(memory_media.file.name).name, "type": media_type, "mimetype": ctype})

    # Render the memory view page
    return render(request, "diarytrove/memory_view.html", {"memory": memory,
                                                           "content": memory.content.strip().split("\n"),
                                                           "mood_emoji": memory.MOODS[memory.mood-1][1],
                                                           "media_data": media_data})


@login_required
def memory_media_view(request:HttpRequest, memory_pk:int, media_pk:int):
    """
    Returns the raw media file if the data is valid and verifications passed
    """
    memory:Memory = get_object_or_404(Memory, pk=memory_pk)
    memory_media:MemoryMedia = get_object_or_404(MemoryMedia, pk=media_pk)

    # Check path consistency
    if memory_media not in memory.memorymedia_set.all():
        raise Http404("The memory doesn't contain this media")
    
    # Verify access rights
    if not(request.user.is_superuser or request.user == memory.owner):
        raise PermissionDenied("You are not the owner of this media")
    
    # Make sure there is a file path
    if memory_media.file:
        file_path = memory_media.file.name
        if not file_path:
            raise Http404("No path associated with the media file")
    else:
        raise Http404("No file associated with the media")
    
    # Everything is in order, return media file response
    return private_media_response(request, Path(file_path))
