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
        from booki import settings

        user = resolve_variable(self.user, context)
        # should check if it exists and etc

        profile = UserProfile.objects.get(user=user)

        if not profile.image:
            return """<img src="%sstatic/_profile_images/_anonymous.jpg"/>""" % settings.MEDIA_URL

        filename = profile.image.name
            
            
        return """<img src="%sstatic/_profile_images/%s"/>""" % (settings.MEDIA_URL, filename.split('/')[-1])

@register.tag
def profile_image(parser, token):
    bits = token.contents.split()

    if len(bits) != 2:
        raise TemplateSyntaxError

    return ProfileImageNode(bits[1])

