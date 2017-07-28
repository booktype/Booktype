from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from booktype.utils import config


# Inspired by https://github.com/mfogel/django-settings-context-processor
def settings_variables(request):
    """
    Adds the settings specified in settings.TEMPLATE_VISIBLE_SETTINGS to
    the request context.
    """
    new_settings = {}

    for attr in getattr(settings, "TEMPLATE_VISIBLE_SETTINGS", ()):
        new_settings[attr] = config.get_configuration(attr, 'NOVALUE')

        if new_settings[attr] == 'NOVALUE':
            m = "TEMPLATE_VISIBLE_SETTINGS: '{0}' does not exist".format(attr)
            raise ImproperlyConfigured(m)

    return new_settings
