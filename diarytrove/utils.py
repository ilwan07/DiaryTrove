from django.conf import settings
from django.http import HttpRequest, HttpResponse, Http404, FileResponse
from django.core.mail import EmailMultiAlternatives
from django.contrib.staticfiles import finders
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from .models import Profile, Memory, MemoryMedia

from pathlib import Path
from threading import Thread
from email.mime.image import MIMEImage
from mimetypes import guess_type
from functools import lru_cache


def check_profiles(user:User=None):
    """
    Make sure that the user has a profile
    Only triggers manually to avoid perofrmance issues
    """
    if user is not None:
        affected_users = [user]
    else:
        affected_users = User.objects.all()
    
    for affected_user in affected_users:
        if not hasattr(affected_user, "profile"):
            profile = Profile(user=affected_user)
            profile.save()


def needs_profile(func) -> callable:
    """
    Decorator to ensures the request user has a profile
    Profile may be missing if the user was created manually
    """
    def wrapper(*args, **kwargs):
        request: HttpRequest = args[0]
        if request.user.is_authenticated:
            check_profiles(request.user)
        return func(*args, **kwargs)
    return wrapper


def safe_join(root:Path, *paths) -> Path:
    """
    Join paths while protecting against directory transversal attacks
    """
    final = root.joinpath(*paths).resolve()
    if not str(final).startswith(str(root.resolve())):
        raise ValueError("Attempted directory traversal")
    return final


def private_media_response(request:HttpRequest, file_path:Path) -> HttpResponse:
    """
    Get a private media file as a file response, only call internally
    Ownership verification must be passed before calling this function
    The file_path is local to the private media directory
    """
    # Resolve the safe absolute path
    try:
        abs_path = safe_join(Path(settings.PRIVATE_MEDIA_ROOT), file_path)
    except ValueError:
        raise Http404("Attempted directory transversal")  # Atempted directory traversal, no results

    if not abs_path.exists() or not abs_path.is_file():
        raise Http404("Cannot find media file")  # The file can't be found

    # In production with Nginx
    if not settings.DEBUG:
        internal_path = f"/internal_protected/{file_path}"  # Matches the Nginx config location
        response = HttpResponse()
        ctype = guess_type(str(abs_path))[0]
        if ctype:
            response["Content-Type"] = ctype
        response["X-Accel-Redirect"] = internal_path
        response["Cache-Control"] = "private, max-age=0, no-cache"  # Header caching
        return response

    # In dev with runserver
    response = FileResponse(open(abs_path, "rb"), as_attachment=False, filename=abs_path.name)
    return response


def memory_media_mimetype(memory_media:MemoryMedia) -> str:
    """
    Get the mimetype of a memory media object
    """
    ctype = guess_type(str(settings.PRIVATE_MEDIA_ROOT / memory_media.file.name))[0]
    if ctype is None:
        return "application/octet-stream"  # Default to binary if no type is found
    return ctype


def memory_to_dict(memory:Memory) -> dict:
    """
    Creates a dict with all the needed information for a memory preview tile
    """
    MAX_CONTENT_CHARS = 1000
    MAX_TITLE_CHARS = 120

    title = memory.title.strip()
    mood_emoji = memory.MOODS[memory.mood-1][1]
    content = memory.content.strip().replace("\n", " ")
    if len(title) > MAX_TITLE_CHARS:
        title = title[:MAX_TITLE_CHARS] + "..."
    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + "..."

    image = memory_preview_image(memory)
    image_pk = image.pk if image is not None else None
    
    return {"pk": memory.pk, "title": title, "date": memory.date,
            "mood_emoji": mood_emoji, "content": content, "image_pk": image_pk}


def memory_preview_image(memory:Memory) -> MemoryMedia|None:
    """
    Gets the first image MemoryMedia for a memory, or None if there's no image
    """
    mediaset = memory.memorymedia_set.all()
    for media in mediaset:
        if memory_media_mimetype(media).startswith("image/"):
            return media
    return None


def send_email(user:User, template:str, subject:str, context:dict={}, sender:str=settings.DEFAULT_FROM_EMAIL, attachments:list[Path]=[]):
    """
    Send an email to a user using a thread by providing the templates directory
    The template directory is under the emails directory, and contains template.txt and template.html
    """
    def send_email_thread():
        text_content = render_to_string(f"diarytrove/emails/{template}/template.txt", context=context)
        html_content = render_to_string(f"diarytrove/emails/{template}/template.html", context=context)
        css_path = finders.find("diarytrove/css/emails.css")
        if css_path:
            with open(css_path, "r", encoding="utf-8") as css_file:
                css = css_file.read()
            html_content = html_content.replace("</head>", f"\n<style>\n{css}\n</style>\n</head>")
        email = EmailMultiAlternatives(subject, text_content, sender, [user.email])
        if html_content is not None:
            email.attach_alternative(html_content, "text/html")
        for attachment in attachments:
            email.attach(file_data(attachment))
        email.send()

    check_profiles(user)  # Ensures the user has a profile and therefore an email language
    context.update({
        "user": user,
        "title": subject,
        "base_url": f"{'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'}://{settings.WEB_DOMAIN}",
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "GITHUB_REPO": settings.GITHUB_REPO,
    })
    email_thread = Thread(target=send_email_thread)
    email_thread.daemon = True
    email_thread.start()


@lru_cache()
def file_data(file_path:Path) -> MIMEImage:
    with open(file_path, "rb") as f:
        data = f.read()
    file = MIMEImage(data)
    file.add_header("Content-ID", f"<{file_path.name}>")
    file.add_header("Content-Disposition", "attachment", filename=file_path.name)
    return file
