from rest_framework.authtoken.views import ObtainAuthToken


class BooktypeViewSetMixin(object):
    """
    This is a mixin used to specify different serializer classes
    for each method action
    """

    def get_serializer_class(self):
        """
        Look for serializer class in self.serializer_action_classes, which
        should be a dict mapping action name (key) to serializer class (value),
        i.e.:

        class MyViewSet(BooktypeViewSetMixin, ViewSet):
            serializer_class = MyDefaultSerializer
            serializer_action_classes = {
               'list': MyListSerializer,
               'my_action': MyActionSerializer
            }

            @action
            def my_action:
                ...

        If there's no entry for that action then just fallback to the regular
        get_serializer_class lookup: self.serializer_class, DefaultSerializer.

        Thanks gonz: http://stackoverflow.com/a/22922156/11440

        """
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super(BooktypeViewSetMixin, self).get_serializer_class()


class AuthToken(ObtainAuthToken):
    """Allow generating an auth token with given username/password."""

    permission_classes = ()
