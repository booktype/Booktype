# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


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


class Role(models.Model):
    """
    Roles are a way to group users and apply some permissions in Booktpe.
    A user as member of the Role automatically has all permissions granted to
    that role.
    """
    name = models.CharField(_('name'), max_length=60, unique=True)
    description = models.CharField(
        _('description'), max_length=255, blank=True
    )
    permissions = models.ManyToManyField(
        Permission, verbose_name=_('permissions'),
        blank=True, null=True
    )
    members = models.ManyToManyField(
        User, verbose_name=_('users'),
        blank=True, null=True,
        related_name='roles'
    )

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
