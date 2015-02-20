from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype account application'),
    'app_name': 'account',
    'permissions': [
        ('can_upload_book', _('Import EPUB/DOCX Books'))
    ]
}
