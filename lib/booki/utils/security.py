# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

from booki.editor import models

class BookiSecurity(object):
    """
    Used to keep security info about user. It is temporarily created and state of this object is not saved anywhere.

    @type user: C{django.contrib.auth.models.User}
    @ivar user: Reference to Booki user
    @type groupPermissions: C{list}
    @ivar groupPermissions: List of group permissions
    @type bookPermissions: C{list}
    @ivar bookPermissions: List of book permissions
    @type isGroupOwner: C{bool}
    @ivar isGroupOwner: Is L{user} also group owner
    @type isBookOwner: C{bool}
    @ivar isBookOwner: Is L{user} also book owner
    """

    def __init__(self, user):
        self.user = user

        self.groupPermissions = []
        self.bookPermissions  = []

        self.isGroupOwner = False
        self.isBookOwner = False

    def isSuperuser(self):
        return self.user.is_superuser

    def isStaff(self):
        return self.user.is_staff

    def isGroupAdmin(self):
        return self.isGroupOwner or (1 in self.groupPermissions) or self.isSuperuser()

    def getGroupPermissions(self):
        return self.groupPermissions

    def getBookPermissions(self):
        return self.bookPermissions

    def isBookAdmin(self):
        return self.isBookOwner or (1 in self.bookPermissions)

    def isAdmin(self):
        return self.isSuperuser() or self.isGroupAdmin() or self.isBookAdmin()



def getUserSecurityForGroup(user, group):
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
    bs.isGroupOwner = group.owner == user

    if user.is_authenticated():
        bs.groupPermissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, group=group)]
    return bs

def getUserSecurityForBook(user, book):
    """
    This functions loads all user permissions for a specific book. It also loads group permissions if L{book} if group is set.

    @type user: C{django.contrib.auth.models.User}
    @param user: Booki user object
    @type book: C{booki.editor.models.Book}
    @param book: Book object

    @rtype: C{booki.utils.security.BookiSecurity}
    @return: BookiSecurity object with loaded permissions
    """

    bs = BookiSecurity(user)
    bs.isBookOwner = user == book.owner

    if user.is_authenticated():
        bs.bookPermissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, book=book)]

    if book.group:
        bs.isGroupOwner = book.group.owner == user
        if user.is_authenticated():
            bs.groupPermissions = [s.permission for s in models.BookiPermission.objects.filter(user=user, group=book.group)]

    return bs

def getUserSecurity(user):
    pass

def canEditBook(book, bookSecurity):
    """
    Check all permissions to see if user defined in L{bookSecurity} can edit L{book}.

    @type book: C{booki.editor.models.Book}
    @param book: Book object
    @type bookSecurity: C{booki.utils.security.BookiSecurity}
    @type bookSecurity: BookSecurity object
    @rtype: C{book}
    @return: Returns True if user can edit this book
    """

    hasPermission = False

    if book.permission == 0:
        hasPermission = True
    elif book.permission == 1 and bookSecurity.isBookOwner:
        hasPermission = True
    elif book.permission == 2 and bookSecurity.isAdmin():
        hasPermission = True
    elif book.permission == 3 and (bookSecurity.isAdmin() or (2 in bookSecurity.bookPermissions)):
        hasPermission = True

    return hasPermission
