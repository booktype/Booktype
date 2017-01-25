from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from .serializers import UserSerializer

from ..tokens import token_generator
from ..views import BooktypeViewSetMixin
from ..security import IsAdminOrIsSelf, BooktypeSecurity


class UserViewSet(
        mixins.CreateModelMixin, mixins.RetrieveModelMixin,
        mixins.UpdateModelMixin, mixins.ListModelMixin,
        BooktypeViewSetMixin, viewsets.GenericViewSet
        ):

    """
    API endpoint that allows users to be viewed or edited.

    list:
    Returns all the users in the system ordered by date joined

    create:
    Allows creating a new user

    retrieve:
    Returns an user instance

    partial_update:
    Executes a partial user instance update

    update:
    Executes a full user instance update
    """

    required_perms = ['api.manage_users']
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    @detail_route(url_path='session-token', permission_classes=[IsAdminOrIsSelf])
    def session_token(self, request, pk=None):
        """
        Returns a login token to be used to authenticate into the booktype
        instance platform.

        For admins:
            In order to use this token you need to set the booktype.api.middleware.AuthMiddleware
            into your MIDDLEWARE_CLASSES and also set the booktype.api.auth.Backend in the
            AUTHENTICATION_BACKENDS setting
        """

        user = self.get_object()
        return Response(
            {'token': token_generator.make_token(user)})
