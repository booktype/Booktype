# -*- coding: utf-8 -*-
import importlib
from booktype.apps.core.models import Permission


def create_permissions(app_name, app_perms, stdout=True):
    """
    Creates or updates the permissions given as parameter into
    Booktype Permissions model

    Args:
        app_name: Booktype application module
        app_perms: List of tuples with the permissions to be registered

    Returns:
        A list with all saved permissions
    """

    perms_app_name = app_perms.get('app_name', app_name)
    permissions = app_perms.get('permissions', None)
    created_perms = []
    if not permissions:
        return created_perms

    if len(permissions) > 0:
        if stdout:
            print "Updating permissions for %s" % app_name

    for codename, description in permissions:
        perm, _ = Permission.objects.get_or_create(
            app_name=perms_app_name,
            name=codename
        )
        perm.description = unicode(description)
        perm.save()
        created_perms.append(perm)
        if stdout:
            print "\t- saving %s.%s permission".expandtabs(4) \
                % (perms_app_name, codename)

    return created_perms


def permissions_for_app(app_name):
    """
    Checks if the application received as parameter has the PERMISSIONS
    constant and return a dict of permissions, otherwise it returns an
    empty dict

    Args:
        app_name: Application name available in settings.INSTALLED_APPS

    Returns:
        A dict with permissions configuration
            e.g: {
                'verbose_name='Group perms verbose',
                'app_name': 'editor',
                'permissions': [
                    ('can_edit', _('Can edit desc')),
                    ('can_delete', _('Can delete desc'))
                ]
            }
    """

    EMPTY = {}
    _perms = 'PERMISSIONS'

    try:
        app = importlib.import_module(app_name)
    except Exception:
        pass
    else:
        if hasattr(app, _perms):
            permissions = getattr(app, _perms)
            if type(permissions) == dict and _perms.lower() in permissions:
                return permissions
    return EMPTY
