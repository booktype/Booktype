from django import template

register = template.Library()

@register.simple_tag
def username(user):
    """Returns full name of the user.

    Args:
        user: User object

    Returns:
        Returns Full name of the user if possible. If user is not authenticated it will return "Anonymous"
        value. If user is authenticated and does not have defined Full name it will return username.
    """

    name = user.username
    if user.is_authenticated():
        if user.first_name.strip() != '':
            name = user.first_name
    else:
        name = 'Anonymous'

    return name
