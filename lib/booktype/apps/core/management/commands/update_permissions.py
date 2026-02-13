# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand

from booktype.apps.core.models import Permission
from booktype.utils.permissions import (
    create_permissions, permissions_for_app
)

BOLD_ON = '\033[1m'
BOLD_OFF = '\033[0m'


class Command(BaseCommand):
    help = 'Reloads permissions for specified apps, or all apps if \
        no args are specified'

    # TODO: load permissions just for one app specified as param

    def add_arguments(self, parser):
        parser.add_argument('--delete-orphans', action='store_true',
                            help='Specify this param to delete undeclared permissions')

    def handle(self, *args, **options):
        saved_perms = []

        for app_name in settings.INSTALLED_APPS:
            app_perms = permissions_for_app(app_name)
            saved_perms += create_permissions(app_name, app_perms)

        saved_perms_ids = [p.pk for p in saved_perms]
        orphan_perms = Permission.objects.exclude(id__in=saved_perms_ids)

        if options['delete_orphans']:
            orphan_perms.delete()
            print(BOLD_ON + "All undeclared permissions has been deleted." + BOLD_OFF)
        else:
            if orphan_perms.count() > 0:
                suggestion = (
                    "There are %s undeclared permissions. "
                    "To delete them use: \n"
                    "./manage.py update_permissions --delete-orphans"
                )
                print(BOLD_ON + suggestion % orphan_perms.count() + BOLD_OFF)
