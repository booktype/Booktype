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

    group_security = security.get_user_security_for_group(user, group)
    is_group_admin = group_security.is_group_admin()

    if group.owner == user or user.is_superuser or is_group_admin:
        return True
    return False