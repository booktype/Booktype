from django.utils.translation import ugettext_lazy as _


PERMISSIONS = {
    'verbose_name': _('Booktype export application'),
    'app_name': 'export',
    'permissions': [
        ('export_book', _('Export book')),
        ('export_settings', _('Change export settings')),
        ('export_view', _('View exported file')),
        ('export_delete', _('Delete exported book')),
        ('export_comment', _('Comment exported files')),
        ('publish_book', _('Publish exported book'))
    ]
}