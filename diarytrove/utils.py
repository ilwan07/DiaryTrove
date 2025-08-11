from django.http import HttpRequest

from . import jobs


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
