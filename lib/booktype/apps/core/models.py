# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from booki.editor.models import Book, Language


class Permission(models.Model):
    """
    Permission system is used by the Booktype app.

    Each app can expose its own set of permissions in the
    __init__.py file
    """
    app_name = models.CharField(_('app name'), max_length=40)
    name = models.CharField(_('name'), max_length=60)
    description = models.CharField(
        _('description'),
        max_length=255
    )

    def __unicode__(self):
        return self.label

    class Meta:
        unique_together = ('app_name', 'name')
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')

    @property
    def label(self):
        """
        Checks if description has an internalized string and returns it.
        Otherwise, it returns the description stored in DB
        """
        from booktype.utils.permissions import permissions_for_app
        app_perms = permissions_for_app(self.app_name)
        if 'permissions' in app_perms:
            for code_name, desc in app_perms.get('permissions'):
                if code_name == self.name:
                    return desc
        return u'%s' % self.description

    @property
    def key_name(self):
        return '%s.%s' % (self.app_name, self.name)


class Role(models.Model):
    """
    Roles are a way to group users and apply some permissions in Booktpe.
    A user as member of the Role automatically has all permissions granted to
    that role
    """
    name = models.CharField(_('name'), max_length=60, unique=True)
    description = models.CharField(
        _('description'), max_length=255, blank=True
    )
    permissions = models.ManyToManyField(
        Permission, verbose_name=_('permissions'),
        blank=True, null=True
    )

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    @property
    def members_count(self):
        return sum([r.members.count() for r in self.bookrole_set.all()])


class BookRole(models.Model):
    """
    Roles for specific books. A user can be 'Editor' in certain book,
    but not in other book. This way we are able to create multiple
    Roles scoped by the desired Book
    """

    role = models.ForeignKey(Role, verbose_name=_('role'))
    book = models.ForeignKey(Book, verbose_name=_('book'))
    members = models.ManyToManyField(
        User, verbose_name=_('users'),
        blank=True, null=True,
        related_name='roles'
    )

    def __unicode__(self):
        return u'%s %s' % (self.book.title, self.role.name)

    class Meta:
        verbose_name = _('Book Role')
        verbose_name_plural = _('Book Roles')


# we're just using to EPUB skeletons for now
# but in near future we're going to implement another
# ways like CSV perhaps
SKELETON_TYPES = (
    (1, _("EPUB")),
)

SKELETON_UPLOAD_DIR = 'book_skeletons/'


class BookSkeleton(models.Model):
    """
    Simple django model to store book skeletons information
    """

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'))

    description = models.CharField(
        _('description'), max_length=255, blank=True)

    language = models.ForeignKey(
        Language, verbose_name=_('Language'))

    skeleton_type = models.IntegerField(
        choices=SKELETON_TYPES,
        verbose_name=_('Skeleton Type'))

    skeleton_file = models.FileField(
        upload_to=SKELETON_UPLOAD_DIR,
        verbose_name=_('File'))

    def __unicode__(self):
        return u'{0} - {1}'.format(self.name, self.language)

    class Meta:
        verbose_name = _('Book Skeleton')
        verbose_name_plural = _('Book Skeletons')
