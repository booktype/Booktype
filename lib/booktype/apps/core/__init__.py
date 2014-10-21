from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype core application'),
    'app_name': 'core',
    'permissions': [
        ('test_perm', _('Just for test')),
        ('test_perm_2', _('Just for test 2'))
    ]
}
