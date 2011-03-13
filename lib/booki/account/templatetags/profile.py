import os

from django.db.models import get_model
from django.template import Library, Node, TemplateSyntaxError, resolve_variable
from django.conf import settings

from booki.account.models import UserProfile

register = Library()

class ProfileImageNode(Node):
    def __init__(self, user):
        self.user = user

    def render(self, context):
        user = resolve_variable(self.user, context)
        # should check if it exists and etc

        profile = UserProfile.objects.get(user=user)

        if not profile.image:
            return """<img src="%s/images/anonymous.jpg"/>""" % settings.SITE_STATIC_URL

        filename = profile.image.name
            
            
        return """<img src="%s/profile_images/%s"/>""" % (settings.DATA_URL, filename.split('/')[-1])

@register.tag
def profile_image(parser, token):
    """
    Django tag. Shows user profile image. If user does not have defined image it will show anonymous image.

    @type token: C{string}
    @param token: Variable name that points to C{User} object.
    """

    bits = token.contents.split()

    if len(bits) != 2:
        raise TemplateSyntaxError

    return ProfileImageNode(bits[1])

