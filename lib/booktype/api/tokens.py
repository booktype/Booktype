from django.contrib.auth.tokens import PasswordResetTokenGenerator


class SessionTokenGenerator(PasswordResetTokenGenerator):
    """
    Simple strategy object that inherits from default PasswordResetTokenGenerator
    used to generate and check tokens for the api authentication/session mechanism.
    """

    key_salt = "booktype.api.tokens.SessionTokenGenerator"

token_generator = SessionTokenGenerator()
