from django.conf import settings
from django.test import TestCase as DjangoTestCase
from django.utils.translation import ugettext_lazy as _

from booktype.apps.core.models import Role, Permission
from booktype.utils import config
from booktype.utils.permissions import create_permissions, permissions_for_app


class TestCase(DjangoTestCase):
    """
    Base class for all old booktype tests.
    """

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)

        self._app_permissions = []
        self._app_roles = []

    def _update_permissions(self):
        for app_name in settings.INSTALLED_APPS:
            app_perms = permissions_for_app(app_name)
            self._app_permissions.append(
                create_permissions(app_name, app_perms, stdout=False)
            )

    def _update_default_roles(self):
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
                perm = Permission.objects.get(app_name=app, name=code_name)
                role.permissions.add(perm)

            self._app_roles.append(role)

    def setUp(self):
        super(TestCase, self).setUp()
        self._update_permissions()
        self._update_default_roles()
