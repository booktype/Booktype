from django.conf import settings

from rest_framework.permissions import BasePermission
from booktype.utils import security


class BaseBooktypePermission(BasePermission):
    """
    Base permission class for using with rest_framework.viewsets
    """

    def get_required_perms(self, view):
        """
        Return a list of required permissions to execute current action.
        `required_perms` property can be defined in 2 ways:
         - as list: `required_perms = ['app.permission']`
         - as dict: `required_perms = {
                        'default': ['app.permission'],
                        'list': ['app.can_list'],
                        'action_something': ['app.can_do_something']
                    }`
        
        :param view: rest_framework.viewsets instance
        :return: list of required permissions
        """

        required_perms = getattr(view, 'required_perms', [])

        if required_perms.__class__ is list:
            return required_perms
        elif required_perms.__class__ is dict:
            if view.action in required_perms:
                return required_perms[view.action]
            else:
                return required_perms['default']
        else:
            raise Exception('"required_perms" property has wrong value.')


class WhitelistIPPermission(BaseBooktypePermission):
    """
    Permission class to check if REMOTE_ADDR which requesting an API resource
    is allowed under a 'white' list of IP. The list will be pulled from django settings
    BOOKTYPE_API_ALLOWED_IPS
    """

    def has_permission(self, request, view):
        ip_addr = request.META['REMOTE_ADDR']
        whitelist = getattr(settings, 'BOOKTYPE_API_ALLOWED_IPS', [])

        # check if api is open to world
        if '*' in whitelist:
            return True

        return ip_addr in whitelist


class BooktypeSecurity(BaseBooktypePermission):
    """Basic security module to use custom booktype permissions"""

    def has_permission(self, request, view):
        """Takes the list of required permissions from the view and
        check if user has them all"""

        required_perms = self.get_required_perms(view)

        if not required_perms:
            return True

        user_security = security.get_security(request.user)
        perms_list = [user_security.has_perm(x) for x in required_perms]

        return all(perms_list)


class BooktypeBookSecurity(BaseBooktypePermission):
    """Basic book security module to use custom booktype permissions"""

    def has_object_permission(self, request, view, obj):
        """Takes the list of required permissions from the view and
        check if user has them all"""

        required_perms = self.get_required_perms(view)
        if not required_perms:
            return True

        book_security = security.get_security_for_book(request.user, obj)
        perms_list = [book_security.has_perm(x) for x in required_perms]

        return all(perms_list)


class IsAdminOrIsSelf(BaseBooktypePermission):
    """
    Object-level permission to only allow superuser or user is same object
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user == obj:
            return True

        return False


class IsAdminOrBookOwner(BaseBooktypePermission):
    """
    Object-level permission to only allow superuser and user is book owner
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user == obj.owner:
            return True

        return False
