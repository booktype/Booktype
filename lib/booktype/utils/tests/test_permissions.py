# -*- coding: utf-8 -*-
from booktype.tests import TestCase
from booktype.utils import permissions
from booktype.apps.core.models import Permission


class PermissionsUtilsTestCase(TestCase):
    """
    Tests all methods in permissions.py module
    """

    def setUp(self):
        self.app_name = 'foo_meh'
        self.PERMS = {
            'permissions': [
                ('test_booktype', 'Can test booktype'),
                ('test_perm', 'Test of permissions'),
            ]
        }

    def test_create_permissions(self):
        # delete permissions before fake
        Permission.objects.all().delete()

        # first, lest create permissions in DB
        permissions.create_permissions(self.app_name, self.PERMS)

        # now check if they are registered
        self.assertEqual(
            Permission.objects.count(),
            len(self.PERMS['permissions']),
            "Registered permissions should be same as in this test case"
        )

        # Let's try to find one specific permission in DB
        self.assertTrue(
            Permission.objects.filter(
                app_name=self.app_name, name='test_booktype'
            ).exists(),
            "This permission should be already registered in DB"
        )

    def test_permissions_for_app(self):
        """
        This only tests if an app that doesn't belongs or exists in
        booktype.apps packages, will return an empty list
        """
        EMPTY = {}
        bad_app_name = 'foo_meh_book'
        self.assertEqual(
            permissions.permissions_for_app(bad_app_name),
            EMPTY,
            "This should return an empty list"
        )
