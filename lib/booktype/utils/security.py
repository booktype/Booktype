from booki.editor import models


class BookiSecurity(object):
    """
    Used to keep security info about user. It is temporarily created and state of this object is not saved anywhere.

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
        return self.is_group_owner or (1 in self.group_permissions) or self.is_superuser()

    def get_group_permissions(self):
        return self.group_permissions

    def get_book_permissions(self):
        return self.book_permissions

    def is_book_admin(self):
        return self.is_book_owner or (1 in self.book_permissions)

    def is_admin(self):
        return self.is_superuser() or self.is_group_admin() or self.is_book_admin()

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
        bs.group_permissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, group=group)]
    return bs


def get_user_security_for_book(user, book):
    """
    This functions loads all user permissions for a specific book. It also loads group permissions if L{book} if group is set.

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
        bs.book_permissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, book=book)]

    if book.group:
        bs.is_group_owner = book.group.owner == user
        if user.is_authenticated():
            bs.group_permissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, group=book.group)]

    return bs


def get_user_security(user):
    pass


def can_edit_book(book, book_security):
    """
    Check all permissions to see if user defined in L{book_security} can edit L{book}.

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
    elif book.permission == 1 and (book_security.is_book_owner or book_security.is_superuser()):
        has_permission = True
    elif book.permission == 2 and book_security.is_admin():
        has_permission = True
    elif book.permission == 3 and (book_security.is_admin() or (2 in book_security.book_permissions)):
        has_permission = True

    return has_permission
