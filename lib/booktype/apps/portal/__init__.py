from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype portal application'),
    'app_name': 'portal',
    'permissions': [
        ('can_view_books_list', _('View books list')),
        ('can_view_group_info', _('View group info')),
        ('can_view_groups_list', _('View groups list')),
        ('can_view_recent_activity', _('View recent activity')),
        ('can_view_user_list', _('View user list')),
    ]
}