# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.


import uuid

from django.template import Library, Node, TemplateSyntaxError, Variable
from django.utils.safestring import mark_safe
from booktype.apps.account import utils

register = Library()


class ProfileImageNode(Node):
    def __init__(self, user):
        self.user = user

    def render(self, context):
        user = Variable(self.user).resolve(context)
        image_url = utils.get_profile_image(user)
        return mark_safe('<img src="{url}?{anti_cache}"/>'.format(url=image_url, anti_cache=str(uuid.uuid4())))


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
