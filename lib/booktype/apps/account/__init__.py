from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype account application'),
    'app_name': 'account',
    'permissions': [
        ('can_upload_book', _('Import from DOCX or EPUB')),
        ('can_view_user_info', _('View user info')),
        ('can_manage_book_skeletons', _('Manage book skeletons'))
    ]
}
