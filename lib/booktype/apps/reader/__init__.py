from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype reader application'),
    'app_name': 'reader',
    'permissions': [
        ('can_view_full_page', _('View full page')),
        ('can_view_hidden_full_page', _('View hidden full page')),

        ('can_view_draft', _('View draft page')),
        ('can_view_hidden_draft', _('View hidden draft page')),

        ('can_view_book_info', _('View Book Info')),
        ('can_view_hidden_book_info', _('View hidden book info')),
    ]
}
