import pytest

from booktype.apps.core.models import Role, Permission
from booktype.utils import config

from ..api import PERMISSIONS


@pytest.fixture()
def assign_api_perms_registered_role():
    role_name = 'registered_users'
    key = 'DEFAULT_ROLE_%s' % role_name
    role_name = config.get_configuration(key, role_name)

    role = Role.objects.get(name=role_name)
    for permission in [i[0] for i in PERMISSIONS['permissions']]:
        perm = Permission.objects.get(app_name=PERMISSIONS['app_name'], name=permission)
        role.permissions.add(perm)


@pytest.fixture()
def assign_api_perms_anonymous_role():
    role_name = 'anonymous_users'
    key = 'DEFAULT_ROLE_%s' % role_name
    role_name = config.get_configuration(key, role_name)
    role, created = Role.objects.get_or_create(name=role_name)

    for permission in [i[0] for i in PERMISSIONS['permissions']]:
        perm = Permission.objects.get(app_name=PERMISSIONS['app_name'], name=permission)
        role.permissions.add(perm)
