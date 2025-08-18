from django.conf import settings
from django.http import HttpRequest, HttpResponse, Http404, FileResponse
from django.contrib.auth.models import User

from .models import Profile, MemoryMedia

from pathlib import Path
from mimetypes import guess_type

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


def needs_profile(func):
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


def safe_join(root:Path, *paths):
    """
    Join paths while protecting against directory transversal attacks
    """
    final = root.joinpath(*paths).resolve()
    if not str(final).startswith(str(root.resolve())):
        raise ValueError("Attempted directory traversal")
    return final


def private_media_response(request:HttpRequest, file_path:Path):
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


def memory_media_mimetype(memory_media:MemoryMedia):
    """
    Get the mimetype of a memory media object
    """
    ctype = guess_type(str(settings.PRIVATE_MEDIA_ROOT / memory_media.file.name))[0]
    if ctype is None:
        return "application/octet-stream"  # Default to binary if no type is found
    return ctype
