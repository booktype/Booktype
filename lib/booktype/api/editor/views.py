from django.contrib.auth.models import User

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from django_filters.rest_framework import DjangoFilterBackend

from booki.editor.models import Book, Language
from booktype.apps.core.models import BookRole, Role

from . import serializers
from ..views import BooktypeViewSetMixin
from ..security import IsAdminOrBookOwner, BooktypeSecurity


class BookViewSet(BooktypeViewSetMixin, viewsets.ModelViewSet):

    """
    API endpoint that allows books to be viewed or edited.

    list:
    Return all the books ordered by creation date

    retrieve:
    Return a language instance

    create:
    Allows creating a new book

    partial_update:
    Executes a partial book instance update

    update:
    Executes a full book instance update

    destroy:
    Allows deleting a book from the system
    """

    required_perms = ['api.manage_books']
    queryset = Book.objects.all().order_by('-created')

    serializer_class = serializers.BookSerializer
    serializer_action_classes = {
        'list': serializers.BookListSerializer,
        'create': serializers.BookCreateSerializer
    }

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['owner_id', 'language_id']

    @detail_route(url_path='users-by-role', permission_classes=[IsAdminOrBookOwner, BooktypeSecurity])
    def users_by_role(self, request, pk=None):
        """
        Returns a list of all roles in the current book with the members assigned
        on each role
        """

        # @TODO: discuss if we should check with book_security module if requesting user has_perms
        # to view the users by role. For now we're just allowing owner and superuser

        # @NOTE we could create a decorator to check some defined permissions and
        # raise a rest_framework.exceptions.PermissionDenied exception from the inside of decorator

        book = self.get_object()
        roles = book.bookrole_set.all()
        serializer = serializers.BookRoleSerializer(
            roles, context={'request': request},
            many=True
        )
        return Response(serializer.data)

    @detail_route(
        methods=['post'], url_path='grant-user',
        permission_classes=[IsAdminOrBookOwner, BooktypeSecurity])
    def grant_user(self, request, pk=None):
        """
        Grants a given user to be part of certain given role name under the
        current book

        parameters:
            -   name: role_name
                required: true
                type: Unique role name to be granted
            -   name: user_id
                required: true
        """
        book = self.get_object()

        try:
            user = User.objects.get(id=request.data['user_id'])
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            role = Role.objects.get(name=request.data['role_name'])
        except Role.DoesNotExist:
            return Response({'detail': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

        book_role, _ = BookRole.objects.get_or_create(
            role=role, book=book)
        book_role.members.add(user)

        serializer = serializers.BookRoleSerializer(
            book_role, context={'request': request})
        return Response(serializer.data)


class LanguageViewSet(
        mixins.RetrieveModelMixin, mixins.ListModelMixin,
        BooktypeViewSetMixin, viewsets.GenericViewSet
        ):

    """
    API endpoint that allows languages to be viewed or listed.

    retrieve:
    Return a language instance

    list:
    Return all the languages
    """

    required_perms = ['api.manage_languages']
    queryset = Language.objects.all()
    serializer_class = serializers.LanguageSerializer
