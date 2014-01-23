from django.conf import settings

def profiles(request):
    try:
        profile = settings.PROFILE_ACTIVE
    except AttributeError:
        profile = ''

    return {'ACTIVE_PROFILE': profile}

