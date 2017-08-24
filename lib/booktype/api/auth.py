from django.contrib.auth.backends import ModelBackend
from .tokens import token_generator


class Backend(ModelBackend):
    """
    Auth Backend to authenticate users with the token genrated via api
    """

    def authenticate(self, pk, token):
        user = self.get_user(pk)
        # if is not a valid user, just return none
        if not user:
            return None

        # check the validity of the token
        if token_generator.check_token(user, token):
            return user

        return None
