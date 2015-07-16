from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype core application'),
    'app_name': 'core',
    'permissions': [
        ('manage_roles', _('Manage Roles')),
        ('manage_permissions', _('Manage Permissions'))
    ]
}
