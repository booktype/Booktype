# -*- coding: utf-8 -*-
from django.test import TestCase
from booktype.apps.core.tests import factory_models

from booktype.utils import security

# permissions constants
APP_NAME = 'foo_meh'
CODE_NAME = 'can_test'


class SecurityUtilsTestCase(TestCase):
    """
    Tests all methods in security.py package
    """

    def setUp(self):
        """
        Sets common attributes for test cases
        """
        self.superuser = factory_models.UserFactory(is_superuser=True)
        self.user = factory_models.UserFactory()

        # create a permission in DB
        self.can_test_permission = factory_models.PermissionFactory(
            app_name=APP_NAME,
            name=CODE_NAME
        )

        # create role with permission
        self.role = factory_models.RoleFactory()
        self.role.permissions.add(self.can_test_permission)

    def test_has_perm(self):
        # superuser has all rights to what he wants
        self.assertTrue(
            security.has_perm(self.superuser, '%s.%s' % (APP_NAME, CODE_NAME)),
            "Superuser always should have all permissions"
        )

        # common user, should not have rights
        self.assertFalse(
            security.has_perm(self.user, '%s.%s' % (APP_NAME, CODE_NAME)),
            "If user doesn't have that role, this should be False"
        )

    def test_has_perm_for_book(self):
        # let's create a book and set it to the role
        # so we can scope permissions just for that book
        book = factory_models.BookFactory()
        self.role.book = book

        # also put user as member of that role
        self.role.members.add(self.user)
        self.role.save()

        permission = '%s.%s' % (APP_NAME, CODE_NAME)
        self.assertTrue(
            security.has_perm(
                self.user, permission, book=book
            ),
            "Member of a book's role should have permissions"
        )
