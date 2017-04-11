from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from booktype.apps.core.models import BookRole, Role
from booktype.utils.security import Security

from . import serializers
from .filters import RoleFilter


class RoleList(generics.ListAPIView):
    """
    API endpoint that lists system global roles.
    """

    model = Role
    serializer_class = serializers.RoleListSerializer
    filter_class = RoleFilter

    def get_queryset(self):
        return Role.objects.all()

    def get(self, request, *args, **kwargs):
        security = Security(request.user)

        if security.has_perm('api.list_roles') or security.has_perm('core.manage_roles'):
            return super(RoleList, self).get(request, *args, **kwargs)

        raise PermissionDenied
