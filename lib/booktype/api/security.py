from django.conf import settings

from rest_framework.permissions import BasePermission
from booktype.utils import security


class WhitelistIPPermission(BasePermission):
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


class BooktypeSecurity(BasePermission):
    """Basic security module to use custom booktype permissions"""

    def has_permission(self, request, view):
        """Takes the list of required permissions from the view and
        check if user has them all"""

        required_perms = getattr(view, 'required_perms', [])
        if len(required_perms) == 0:
            return True

        user_security = security.get_security(request.user)
        perms_list = [user_security.has_perm(x) for x in required_perms]

        return all(perms_list)


class IsAdminOrIsSelf(BasePermission):
    """
    Object-level permission to only allow superuser or user is same object
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user == obj:
            return True

        return False


class IsAdminOrBookOwner(BasePermission):
    """
    Object-level permission to only allow superuser and user is book owner
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user == obj.owner:
            return True

        return False
