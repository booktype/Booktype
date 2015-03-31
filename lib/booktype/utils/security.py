# -*- coding: utf-8 -*-
from booktype.utils import config
from booki.editor.models import BookiPermission
from booktype.apps.core.models import Permission, Role


def has_perm(user, to_do, book=None):
    """
    Checks if a given user has rights to execute an specific
    task or action.

    Args:
        user: Django user instance
        to_do: Concatenated string of app name and permission codename
            e.g. "editor.create_chapter"
        book: Optional book instance to scope permissions

    Returns:
        Boolean
    """

    # god mode enabled?
    if user.is_superuser:
        return True

    try:
        app_name, codename = to_do.split('.')
        permission = Permission.objects.get(
            app_name=app_name,
            name=codename
        )
    except ValueError:
        raise Exception("to_do parameter should be 'app_name.permission' way")
    except Permission.DoesNotExist:
        return False
    else:
        permissions = []
        # get default role key for extra permissions
        role_key = get_default_role_key(user)
        default_role = get_default_role(role_key, book)

        # append permissions from default role, no matter if book or not
        if default_role:
            permissions += [p for p in default_role.permissions.all()]

        if user.is_authenticated():
            bookroles = user.roles.all()
            if book:
                bookroles = bookroles.filter(book=book)
            for bookrole in bookroles:
                permissions += [p for p in bookrole.role.permissions.all()]
        return (permission in permissions)

    return False


def get_user_permissions(user, book):
    """
    Returns a list with keynames of permissions for a given user
    in a specific book
    """

    permissions = []

    # get default role key for extra permissions on this book
    role_key = get_default_role_key(user)
    default_role = get_default_role(role_key, book)
    if default_role:
        permissions += [p.key_name for p in default_role.permissions.all()]

    if user.is_authenticated():
        bookroles = user.roles.filter(book=book)
        for bookrole in bookroles:
            permissions += [
                p.key_name for p in bookrole.role.permissions.all()
            ]

    return permissions


def get_default_role_key(user):
    """
    Returns the defaults booktype app role key for given user
    even if is not registered
    """
    if user.is_authenticated():
        role_key = 'registered_users'
    else:
        role_key = 'anonymous_users'

    return role_key


def get_default_role(key, book=None):
    """
    Returns default role if exists one already registered
    in system database, otherwise returns None
    """

    default_role = None
    default_key = 'DEFAULT_ROLE_%s' % key
    role_name = None

    if book:
        try:
            role_name = book.settings.get(name=default_key).get_value()
        except:
            pass

    if not role_name:
        role_name = config.get_configuration(
            default_key, key)

    # no_role means restricted
    if role_name == '__no_role__':
        return None

    try:
        default_role = Role.objects.get(name=role_name)
    except:
        pass

    return default_role


class Security(object):
    """Base security object for doing security checks.

    User is supposed to inherit this object and use it for custom security checks.
    """

    def __init__(self, user):
        """Initialize base security object.

        :Args:
         - user (:class:`django.contrib.auth.models.User`) - User object
        """
        self.user = user

    def is_superuser(self):
        """Checks if user is Django superuser or not.

        :Returns:
         - Returns True is user is superuser.
        """
        return self.user.is_superuser

    def is_staff(self):
        """Checks if user is Django staff member or not.

        :Returns:
         - Returns True if user is staff member.
        """
        return self.user.is_staff

    def is_admin(self):
        """Checks is user is any kind of admin.

        :Returns:
         - Returns True is user is superuser.
        """
        return self.is_superuser()

    def has_perm(perm):
        return False


class BookSecurity(Security):
    """Basic Book security class.

    User is supposed to communicate with instance of this class to check user permissions.
    """

    def __init__(self, user, book):
        """Initialize Book security object.

        :Args:
         - user (:class:`django.contrib.auth.models.User`): User object
         - book (:class:`booki.editor.models.Book`): Book object object
        """
        super(BookSecurity, self).__init__(user)

        self.book = book

    def is_admin(self):
        """Checks if user is some kind of Book admin.

        User is Book admin if it is owner or superuser.

        :Returns:
         - True if user is some kind of admin."""
        return super(BookSecurity, self).is_admin() or self.is_book_admin()

    def is_book_admin(self):
        """Checks if user is book admin.

        For now user is Book admin if it is Book owner.

        :Returns:
         - True if user is book admin.
        """
        return self.is_book_owner()

    def is_book_owner(self):
        """Checks if user is Book owner.

        User is book owner if it has created the book.

        :Returns:
         - True if user is book owner.
        """
        return self.book.owner == self.user

    def has_perm(self, perm):
        """Check user permissions.

        The difference is this method will also check if user is Book administrator. In case
        user is Book administrator, it will get any kind of permissions they ask for.

        :Args:
         - perm (str): permission to check for

        :Returns:
         Returns True or False.
        """
        if self.is_admin():
            return True
        return has_perm(self.user, perm, self.book)

    def can_edit(self):
        # This always returns True
        # We should check in mode the book is, and then according to it
        # return if this user is allowed to edit this book.
        # Thirt part has not been implemented yet.
        return True


class GroupSecurity(Security):
    """Basic Group security class.

    User is supposed to communicate with instance of this class to check user permissions.
    """

    def __init__(self, user, group):
        """Initialize Book security object.

        :Args:
         - user (:class:`django.contrib.auth.models.User`): User object
         - group (:class:`booki.editor.models.BookiGroup`): Group object object
        """
        super(GroupSecurity, self).__init__(user)

        self.group = group

    def is_admin(self):
        """Checks if user is some kind of Group admin.

        User is Group admin if it is owner or superuser.

        :Returns:
         - True if user is some kind of admin."""
        return super(GroupSecurity, self).is_admin() or self.is_group_admin()

    def is_group_admin(self):
        """Checks if user is group admin.

        For now user is Group admin if it is Group owner.

        :Returns:
         - True if user is group admin.
        """
        return self.is_group_owner()

    def is_group_owner(self):
        """Checks if user is Group owner.

        User is group owner if it has created the group.

        :Returns:
         - True if user is group owner.
        """
        print '========='
        print self.group.owner
        print self.user
        return self.group.owner == self.user


def get_security_for_book(user, book):
    """Returns Book security object for specified user.

    :Args:
     - user (:class:`django.contrib.auth.models.User`): User object
     - book (:class:`booki.editor.models.Book`): Book object object

    :Returns:
     Returns Book security object (:class:`BookSecurity`).
    """
    return BookSecurity(user, book)


def get_security_for_group(user, group):
    """Returns Book security object for specified user.

    :Args:
     - user (:class:`django.contrib.auth.models.User`): User object
     - group (:class:`booki.editor.models.BookiGroup`): Group object object

    :Returns:
     Returns Group security object (:class:`GroupSecurity`).
    """
    return GroupSecurity(user, group)


################################################
# Obsolete API
################################################

class BookiSecurity(object):
    """
    Used to keep security info about user. It is temporarily created
    and state of this object is not saved anywhere.

    @type user: C{django.contrib.auth.models.User}
    @ivar user: Reference to Booki user
    @type group_permissions: C{list}
    @ivar group_permissions: List of group permissions
    @type book_permissions: C{list}
    @ivar book_permissions: List of book permissions
    @type is_group_owner: C{bool}
    @ivar is_group_owner: Is L{user} also group owner
    @type is_book_owner: C{bool}
    @ivar is_book_owner: Is L{user} also book owner
    """

    def __init__(self, user):
        self.user = user

        self.group_permissions = []
        self.book_permissions = []

        self.is_group_owner = False
        self.is_book_owner = False

        # Obsolete API
        self.groupPermissions = self.group_permissions
        self.bookPermissions = self.book_permissions
        self.isGroupOwner = self.is_group_owner
        self.isBookOwner = self.is_book_owner

    def is_superuser(self):
        return self.user.is_superuser

    def is_staff(self):
        return self.user.is_staff

    def is_group_admin(self):
        return (
            self.is_group_owner or
            1 in self.group_permissions or
            self.is_superuser()
        )

    def get_group_permissions(self):
        return self.group_permissions

    def get_book_permissions(self):
        return self.book_permissions

    def is_book_admin(self):
        return self.is_book_owner or (1 in self.book_permissions)

    def is_admin(self):
        return (
            self.is_superuser() or
            self.is_group_admin() or
            self.is_book_admin()
        )

    # Obsolete API
    isSuperuser = is_superuser
    isStaff = is_staff
    isGroupAdmin = is_group_admin
    getGroupPermissions = get_group_permissions
    getBookPermissions = get_book_permissions
    isBookAdmin = is_book_admin
    isAdmin = is_admin


def get_user_security_for_group(user, group):
    """
    This functions loads all user permissions for a specific group.

    @type user: C{django.contrib.auth.models.User}
    @param user: Booki user object
    @type group: C{booki.editor.models.BookiGroup}
    @param group: Booki group object

    @rtype: C{booki.utils.security.BookiSecurity}
    @return: BookiSecurity object with loaded permissions
    """

    bs = BookiSecurity(user)
    bs.is_group_owner = group.owner == user

    if user.is_authenticated():
        for s in BookiPermission.objects.filter(user=user, group=group):
            bs.group_permissions.append(s.permission)
    return bs


def get_user_security_for_book(user, book):
    """
    This functions loads all user permissions for a specific book.
    It also loads group permissions if L{book} if group is set.

    @type user: C{django.contrib.auth.models.User}
    @param user: Booki user object
    @type book: C{booki.editor.models.Book}
    @param book: Book object

    @rtype: C{booktype.utils.security.BookiSecurity}
    @return: BookiSecurity object with loaded permissions
    """

    bs = BookiSecurity(user)
    bs.is_book_owner = user == book.owner

    if user.is_authenticated():
        for s in BookiPermission.objects.filter(user=user, book=book):
            bs.book_permissions.append(s.permission)

    if book.group:
        bs.is_group_owner = book.group.owner == user
        _u = user
        if user.is_authenticated():
            for s in BookiPermission.objects.filter(user=_u, group=book.group):
                bs.group_permissions.append(s.permission)

    return bs


def get_user_security(user):
    pass


def can_edit_book(book, book_security):
    """
    Check all permissions to see if user defined in
    L{book_security} can edit L{book}.

    @type book: C{booki.editor.models.Book}
    @param book: Book object
    @type book_security: C{booktype.utils.security.BookiSecurity}
    @type book_security: BookiSecurity object
    @rtype: C{book}
    @return: Returns True if user can edit this book
    """

    has_permission = False

    if book.permission == 0:
        has_permission = True
    elif (
        book.permission == 1 and
        (book_security.is_book_owner or book_security.is_superuser())
    ):
        has_permission = True
    elif book.permission == 2 and book_security.is_admin():
        has_permission = True
    elif (
        book.permission == 3 and
        (book_security.is_admin() or (2 in book_security.book_permissions))
    ):
        has_permission = True

    return has_permission
