# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.management.base import BaseCommand, CommandError

from booktype.apps.core.models import Permission, Role
from booktype.utils import config


class Command(BaseCommand):
    help = 'Creates or updates default roles on Booktype instance'

    def handle(self, *args, **options):
        for role_name, perms in settings.BOOKTYPE_DEFAULT_ROLES.items():
            # check if there any existing default role already in configuration
            key = 'DEFAULT_ROLE_%s' % role_name
            role_name = config.get_configuration(key, role_name)
            role, created = Role.objects.get_or_create(name=role_name)

            if created:
                role.description = _('system default role')
                role.save()

            for perm in perms:
                app, code_name = perm.split('.')
                try:
                    perm = Permission.objects.get(app_name=app, name=code_name)
                    role.permissions.add(perm)
                except Permission.DoesNotExist:
                    err_msg = 'Create permissions before updating default roles'
                    raise CommandError(err_msg)

            statuses = ['updated', 'created']
            print 'Role %s has been %s.' % (role_name, statuses[created])
