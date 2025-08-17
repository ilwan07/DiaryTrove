from django.conf import settings
from django.http import HttpRequest, HttpResponse, Http404, FileResponse

from . import jobs

from pathlib import Path
from mimetypes import guess_type


def regular_jobs(func):
    """
    Do some regular jobs for authenticated users
    Ensures the backend is ready for the request
    """
    def wrapper(*args, **kwargs):
        request: HttpRequest = args[0]
        if request.user.is_authenticated:
            # Execute important jobs
            jobs.check_profiles(request.user)
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
        ctype, encoding = guess_type(str(abs_path))
        if ctype:
            response["Content-Type"] = ctype
        response["X-Accel-Redirect"] = internal_path
        response["Cache-Control"] = "private, max-age=0, no-cache"  # Header caching
        return response

    # In dev with runserver
    response = FileResponse(open(abs_path, "rb"), as_attachment=False, filename=abs_path.name)
    return response
