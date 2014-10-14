# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings

from booktype.utils.permissions import (
    create_permissions, permissions_for_app
)


class Command(BaseCommand):
    help = 'Reloads permissions for specified apps, or all apps if \
        no args are specified'

    # TODO: load permissions just for one app specified as param

    def handle(self, *args, **options):
        for app_name in settings.INSTALLED_APPS:
            perms = permissions_for_app(app_name)
            create_permissions(app_name, perms)
