# -*- coding: utf-8 -*-
import logging

from booktype.utils import config
from booktype.apps.core.models import Permission, Role

logger = logging.getLogger('booktype.utils.security.base')


class BaseSecurity(object):
    """Base security object for doing security checks.

    User is supposed to inherit this object and use it for custom security checks.
    """

    def __init__(self, user):
        """Initialize base security object.

        :Args:
         - user (:class:`django.contrib.auth.models.User`) - User object
        """
        self.user = user
        self.permissions = []

    def is_superuser(self):
        """Checks if user is Django superuser or not.

        :Returns:
         - Returns True if user is superuser.
        """
        return self.user.is_superuser

    def is_staff(self):
        """Checks if user is Django staff member or not.

        :Returns:
         - Returns True if user is staff member.
        """
        return self.user.is_staff

    def is_admin(self):
        """Checks is user is any kind of admin.

        :Returns:
         - Returns True if user is superuser.
        """
        return self.is_superuser()

    @staticmethod
    def get_permission_from_string(permission_string):
        """Retrieving permission instance based on permission string

        :Args:
          - permission_string (:class:`str`): Concatenated string of app name and permission codename
                                              e.g. "editor.create_chapter"

        :Returns:
          Returns (:class:`booktype.apps.core.models.Permission`) instance or None

        :Raises:
          Exception: If wrong permission string was provided
        """
        try:
            app_name, codename = permission_string.split('.')
            return Permission.objects.get(app_name=app_name, name=codename)
        except ValueError:
            raise Exception("permission_string parameter should be 'app_name.permission' way")
        except Permission.DoesNotExist:
            return None

    def _get_default_role(self, book=None):
        """
        Returns the default role to get extra permissions
        """
        role_key = get_default_role_key(self.user)
        return get_default_role(role_key, book)

    def _get_permissions(self, book=None):
        """Retrieving permissions set

        :Args:
          - book (:class:`booki.editor.models.Book`): Book instance. Optional.

        :Returns:
          Returns (:class:`set`) Set of permissions
        """
        permissions = set()
        default_role = self._get_default_role(book)

        # append permissions from default role, no matter if book or not
        if default_role:
            permissions.update([p for p in default_role.permissions.all()])

        if self.user.is_authenticated():
            if book:
                bookroles = self.user.roles.filter(book=book)
                for bookrole in bookroles:
                    permissions.update([p for p in bookrole.role.permissions.all()])
        return permissions

    def has_perm(self, perm):
        """
        Checks if a given user has rights to execute an specific
        task or action.

        Args:
            perm: Concatenated string of app name and permission codename
                e.g. "editor.create_chapter"

        Returns:
            Boolean
        """

        if self.is_admin():
            return True

        # convert concatenated app name and permission codename string to permission instance
        permission = self.get_permission_from_string(perm)
        if not permission:
            return False

        # query permissions only once
        if not self.permissions:
            self.permissions = self._get_permissions()

        return permission in self.permissions


def get_default_role_key(user):
    """
    Returns the defaults booktype app role key for given user
    even if is not registered
    """
    if user.is_authenticated():
        role_key = 'registered_users'
    else:
        role_key = 'anonymous_users'

    return role_key


def get_default_role(key, book=None):
    """
    Returns default role if exists one already registered
    in system database, otherwise returns None
    """

    default_role = None
    default_key = 'DEFAULT_ROLE_%s' % key
    role_name = None

    if book:
        try:
            role_name = book.settings.get(name=default_key).get_value()
        except:
            logger.info("There is no Role name for role_key %s" % default_key)

    if not role_name:
        role_name = config.get_configuration(
            default_key, key)

    # no_role means restricted
    if role_name == '__no_role__':
        return None

    try:
        default_role = Role.objects.get(name=role_name)
    except:
        logger.info("Role with %s name does not exists" % role_name)

    return default_role
