from django.conf import settings

def contact_email(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'CONTACT_EMAIL': settings.CONTACT_EMAIL}
