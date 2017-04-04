# -*- coding: utf-8 -*-
import mock

from booktype.tests import TestCase
from booktype.tests.factory_models import (UserFactory, PermissionFactory, BookRoleFactory, BookFactory, RoleFactory,
                                           BookGroupFactory)
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
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()

        # create a permission in DB
        self.can_test_permission = PermissionFactory(
            app_name=APP_NAME,
            name=CODE_NAME
        )

        # create role with permission
        self.bookrole = BookRoleFactory()
        self.role = self.bookrole.role
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
        book = BookFactory()
        self.bookrole.book = book

        # also put user as member of that role
        self.bookrole.members.add(self.user)
        self.bookrole.save()

        permission = '%s.%s' % (APP_NAME, CODE_NAME)
        self.assertTrue(
            security.has_perm(
                self.user, permission, book=book
            ),
            "Member of a book's role should have permissions"
        )

    def test_user_security_not_admin(self):
        # let's create a book and set it to the role
        # so we can scope permissions just for that book
        book = BookFactory()
        self.bookrole.book = book

        # also put user as member of that role
        self.bookrole.members.add(self.user)
        self.bookrole.save()

        sec = security.get_security_for_book(self.user, book)

        self.assertFalse(sec.is_admin())

    def test_user_security_is_admin(self):
        # let's create a book and set it to the role
        # so we can scope permissions just for that book
        book = BookFactory()
        self.bookrole.book = book

        # also put user as member of that role
        self.bookrole.members.add(self.superuser)
        self.bookrole.save()

        sec = security.get_security_for_book(self.superuser, book)

        self.assertTrue(sec.is_admin())

    def test_user_security_is_bookowner(self):
        # let's create a book and set it to the role
        # so we can scope permissions just for that book
        book = BookFactory(owner=self.user)

        sec = security.get_security_for_book(self.user, book)

        self.assertTrue(sec.is_book_owner())

    def test_user_security_is_not_bookowner(self):
        # let's create a book and set it to the role
        # so we can scope permissions just for that book
        book = BookFactory(owner=self.superuser)

        sec = security.get_security_for_book(self.user, book)

        self.assertFalse(sec.is_book_owner())

    def test_get_security(self):
        # let's test helper for retrieving base Security instance
        self.assertEqual(security.base.BaseSecurity(self.user).__class__,
                         security.get_security(self.user).__class__)

    def test_get_security_for_book(self):
        # let's test helper for retrieving BookSecurity instance
        self.assertEqual(security.BookSecurity(self.user, self.bookrole.book).__class__,
                         security.get_security_for_book(self.user, self.bookrole.book).__class__)

    def test_get_security_for_group(self):
        # let's test helper for retrieving BookSecurity instance
        group = self.bookrole.book.group
        self.assertEqual(security.GroupSecurity(self.user, group).__class__,
                         security.get_security_for_group(self.user, group).__class__)


class SecurityClassTestCase(TestCase):
    """
    Test for base Security class
    """

    def setUp(self):
        """
        Sets common attributes for test cases
        """
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()
        self.staffuser = UserFactory(is_staff=True)

        # create a permission in DB
        self.can_test_permission = PermissionFactory(app_name=APP_NAME,
                                                     name=CODE_NAME)

        # create role with permission
        self.bookrole = BookRoleFactory()
        self.role = self.bookrole.role
        self.role.permissions.add(self.can_test_permission)

        # add bookrole to common user
        self.user.roles.add(self.bookrole)

        # create role "registered_user"
        self.role_registered_user = RoleFactory()
        # create "content.register" permission
        self.can_content_register_permission = PermissionFactory(app_name="content",
                                                                 name="register")
        # add permission to role
        self.role_registered_user.permissions.add(self.can_content_register_permission)

    def test_is_superuser(self):
        # let's check is_superuser method for superuser
        sec = security.get_security(self.superuser)
        self.assertTrue(sec.is_superuser())

        # let's check is_superuser method for common user
        sec = security.get_security(self.user)
        self.assertFalse(sec.is_superuser())

    def test_is_admin(self):
        # let's check is_admin method for superuser
        sec = security.get_security(self.superuser)
        self.assertTrue(sec.is_superuser())

        # let's check is_admin method for common user
        sec = security.get_security(self.user)
        self.assertFalse(sec.is_superuser())

    def test_is_staff(self):
        # let's check is_staff method for non staff user
        sec = security.get_security(self.user)
        self.assertFalse(sec.is_staff())

        # let's check is_staff method for staff user
        sec = security.get_security(self.staffuser)
        self.assertTrue(sec.is_staff())

    def test_get_permission_from_string(self):
        # get permission by name
        permission = security.base.BaseSecurity.get_permission_from_string(
            "{app}.{name}".format(app=APP_NAME, name=CODE_NAME))
        self.assertEqual(permission, self.can_test_permission)

        # try to get permission with wrong argument
        self.assertRaises(Exception,
                          security.base.BaseSecurity.get_permission_from_string, "can_do_everything")

        # try to get net existing permission
        self.assertFalse(security.base.BaseSecurity.get_permission_from_string("fake.permission"))

    def test_get_permissions_success(self):
        # mock get_default_role function
        security.base.get_default_role = mock.Mock(return_value=self.role_registered_user)

        sec = security.get_security(self.user)
        self.assertIn(self.can_content_register_permission, sec._get_permissions())

        # check that there are no permissions from book
        self.assertNotIn(self.can_test_permission, sec._get_permissions())

    def test_get_permissions_fail(self):
        # mock get_default_role function
        security.base.get_default_role = mock.Mock(return_value=self.role)

        sec = security.get_security(self.superuser)
        self.assertNotIn(self.can_content_register_permission, sec._get_permissions())

    def test_get_permissions_with_book(self):
        # get permissions from default role and from bookrole

        # mock get_default_role function
        security.base.get_default_role = mock.Mock(return_value=self.role_registered_user)

        sec = security.get_security(self.user)
        permissions = sec._get_permissions(book=self.bookrole.book)
        self.assertIn(self.can_content_register_permission, permissions)
        self.assertIn(self.can_test_permission, permissions)

    def test_has_perm(self):
        # security for superuser
        sec = security.get_security(self.superuser)

        # superuser has all rights to what he wants
        self.assertTrue(sec.has_perm('%s.%s' % (APP_NAME, CODE_NAME)),
                        "Superuser always should have all permissions")

        self.assertTrue(sec.has_perm("fake.permission"),
                        "Superuser always should have all permissions")

        # security for common user
        sec = security.get_security(self.user)

        # common user, should not have rights
        self.assertFalse(sec.has_perm('%s.%s' % (APP_NAME, CODE_NAME)),
                         "If user doesn't have that role, this should be False")

        # common user, should have rights
        # mock get_default_role function
        security.base.get_default_role = mock.Mock(return_value=self.role_registered_user)
        self.assertTrue(sec.has_perm("content.register"),
                        "If user doesn't have that role, this should be False")


class BookSecurityClassTestCase(SecurityClassTestCase):
    """
    Test for BookSecurity class
    """

    def setUp(self):
        """
        Sets common attributes for test cases
        """
        super(BookSecurityClassTestCase, self).setUp()

        # add owner to book
        self.bookrole.book.owner = self.user

    def test_is_book_admin(self):
        # user is book admin
        sec = security.BookSecurity(self.user, self.bookrole.book)
        self.assertTrue(sec.is_book_admin())

        # staffuser is not book admin
        sec = security.BookSecurity(self.staffuser, self.bookrole.book)
        self.assertFalse(sec.is_book_admin())

    def test_is_book_owner(self):
        # user is book owner
        sec = security.BookSecurity(self.user, self.bookrole.book)
        self.assertTrue(sec.is_book_owner())

        # staffuser is not book owner
        sec = security.BookSecurity(self.staffuser, self.bookrole.book)
        self.assertFalse(sec.is_book_owner())

    def test_has_perm(self):
        # security for common user
        sec = security.get_security_for_book(self.user, self.bookrole.book)

        # common user, should have rights from book
        self.assertTrue(sec.has_perm('%s.%s' % (APP_NAME, CODE_NAME)),
                        "If user doesn't have that role, this should be False")


class GroupSecurityClassTestCase(SecurityClassTestCase):
    """
    Test for GroupSecurity class
    """

    def setUp(self):
        """
        Sets common attributes for test cases
        """
        super(GroupSecurityClassTestCase, self).setUp()

        self.group = BookGroupFactory()
        self.group.owner = self.user

    def test_is_group_admin(self):
        # user is group admin
        sec = security.get_security_for_group(self.user, self.group)
        self.assertTrue(sec.is_group_admin())

        # superuser is not group admin
        sec = security.get_security_for_group(self.superuser, self.group)
        self.assertFalse(sec.is_group_admin())

        # staff user is not group admin
        sec = security.get_security_for_group(self.staffuser, self.group)
        self.assertFalse(sec.is_group_admin())

    def test_is_group_owner(self):
        # user is group owner
        sec = security.get_security_for_group(self.user, self.group)
        self.assertTrue(sec.is_group_owner())

        # superuser is not group owner
        sec = security.get_security_for_group(self.superuser, self.group)
        self.assertFalse(sec.is_group_owner())

        # staff user is not group owner
        sec = security.get_security_for_group(self.staffuser, self.group)
        self.assertFalse(sec.is_group_owner())
