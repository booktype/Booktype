from django.utils.translation import ugettext_lazy as _

PERMISSIONS = {
    'verbose_name': _('Booktype edit application'),
    'app_name': 'edit',
    'permissions': [
        ('create_chapter', _('Create chapter')),
        ('rename_chapter', _('Rename chapter')),
        ('delete_chapter', _('Delete chapter')),
        ('lock_chapter', _('Lock chapter')),
        ('edit_locked_chapter', _('Edit locked chapter')),

        ('create_section', _('Create section')),
        ('rename_section', _('Rename section')),
        ('delete_section', _('Delete section')),

        ('manage_chapters_hold', _('Manage chapters on hold')),
        ('reorder_toc', _('Reorder TOC')),

        ('upload_attachment', _('Upload attachment')),
        ('remove_attachment', _('Remove attachment')),

        ('upload_cover', _('Upload cover')),
        ('edit_cover', _('Edit cover')),
        ('delete_cover', _('Delete cover')),

        ('export_book', _('Export book')),
        ('publish_book', _('Publish book')),

        ('manage_status', _('Manage Status')),
        ('change_chapter_status', _('Change chapter status')),

        ('delete_book', _('Delete book')),
    ]
}
