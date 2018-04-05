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
        ('export_chapter_content', _('Export chapter content')),
        ('import_to_chapter', _('Import documents to chapters')),

        ('create_section', _('Create section')),
        ('rename_section', _('Rename section')),
        ('delete_section', _('Delete section')),

        ('manage_chapters_hold', _('Manage chapters on hold')),
        ('reorder_toc', _('Reorder TOC')),

        ('upload_attachment', _('Upload attachment')),
        ('remove_attachment', _('Remove attachment')),
        ('rename_attachment', _('Rename attachment')),

        ('upload_cover', _('Upload cover')),
        ('edit_cover', _('Edit cover')),
        ('delete_cover', _('Delete cover')),

        ('manage_status', _('Manage Status')),
        ('change_chapter_status', _('Change chapter status')),

        ('edit_book', _('Edit book')),
        ('delete_book', _('Delete book')),

        ('history_revert', _('Restore history')),
        ('note_edit', _('Edit Notes')),

        ('track_changes', _('Track Changes')),
        ('track_changes_approve', _('Track Changes accept/decline')),
        ('track_changes_enable', _('Track Changes on/off')),

        # permissions for settings interface
        ('manage_language', _('Manage Language')),
        ('manage_license', _('Manage License')),
        ('manage_metadata', _('Manage Metadata')),
        ('manage_book_settings', _('Manage Book Settings')),

        ('add_comment', _('Add Comments')),
        ('resolve_comment', _('Resolve Comments')),
        ('delete_comment', _('Delete Comments')),

        ('modify_section_settings', _('Modify Section Settings')),
        ('generate_invite_code', _('Generate Invite Code')),
    ]
}
