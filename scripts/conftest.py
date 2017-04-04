import pytest

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from booktype.apps.core.models import Role, Permission
from booktype.utils import config
from booktype.utils.permissions import create_permissions, permissions_for_app
from booktype.utils.misc import booktype_slugify
from booktype.tests.factory_models import BookFactory


# # *************** #
# # *** EXAMPLE *** #
# # *************** #
# @pytest.mark.django_db
# class TestExample:
#     @pytest.mark.parametrize('superusers', [('john', 'jack')], indirect=True)
#     @pytest.mark.parametrize('registered_users', [('bob', 'max')], indirect=True)
#     def test_rand_one(self, superusers, registered_users):
#         """
#         Just an example
#         :param superusers: {'john': <User: john>, 'jack': <User: jack>}
#         :param registered_users: {'max': <User: max>, 'bob': <User: bob>}
#         :return:
#         """
#         assert False


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # update_permissions
        for app_name in settings.INSTALLED_APPS:
            app_perms = permissions_for_app(app_name)
            create_permissions(app_name, app_perms, stdout=False)

        # update_default_roles
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


@pytest.fixture()
def superusers(request):
    users = {}
    for name in request.param:
        users[name] = User.objects.create(
            username=name,
            first_name=name.capitalize(),
            last_name=name.capitalize(),
            email="{}@superuser.com".format(name),
            is_staff=True,
            is_superuser=True,
            is_active=True
        )

    return users


@pytest.fixture()
def registered_users(request):
    users = {}
    for name in request.param:
        users[name] = User.objects.create(
            username=name,
            first_name=name.capitalize(),
            last_name=name.capitalize(),
            email="{}@superuser.com".format(name),
            is_staff=False,
            is_superuser=False,
            is_active=True
        )

    return users


@pytest.fixture()
def books(request):
    books = []
    for title in request.param:
        books.append(
            BookFactory(title=title, url_title=booktype_slugify(title))
        )
    return books
