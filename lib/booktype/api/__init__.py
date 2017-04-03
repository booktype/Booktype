from django.utils.translation import ugettext_lazy as _

# TODO: discuss if you should better move to django permissions

PERMISSIONS = {
    'verbose_name': _('Booktype API'),
    'app_name': 'api',
    'permissions': [
        ('generate_token', _('Generate Auth Token')),
        ('review_api_docs', _('Can Review API docs')),
        ('manage_users', _('Manage users')),
        ('manage_books', _('Manage Books')),
        ('manage_languages', _('Manage Languages')),
        ('list_chapters', _('List Chapters')),
        ('create_chapters', _('Create Chapters')),
        ('update_chapters', _('Update Chapters')),
        ('delete_chapters', _('Delete Chapters')),
    ]
}
