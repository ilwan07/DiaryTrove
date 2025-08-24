from django.conf import settings

def global_variables(request):
    """
    Makes some variables available to any template
    """
    return {"CONTACT_EMAIL": settings.CONTACT_EMAIL,
            "GITHUB_REPO": settings.GITHUB_REPO}
