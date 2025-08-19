from django.conf import settings

def contact_email(request):
    """
    Makes the contact email available to any template
    """
    return {'CONTACT_EMAIL': settings.CONTACT_EMAIL}
