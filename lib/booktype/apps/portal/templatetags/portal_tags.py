from django.template import Library
from booktype.utils import security

register = Library()

@register.assignment_tag
def can_delete_group(group, user):
    """
    Checks if a given user has enough rights to delete a group
    :param group: booki.editor.models.BookiGroup instance
    :param user: django.contrib.auth.models.User instance
    :returns: Boolean
    """

    group_security = security.get_security_for_group(user, group)

    return group_security.is_group_admin()
