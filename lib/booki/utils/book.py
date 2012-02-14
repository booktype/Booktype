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

import datetime

from booki.utils.misc import bookiSlugify
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from booki.editor import models
from booki.utils.log import logBookHistory


def checkBookAvailability(bookTitle):
    """
    Checks if the book name is available or not.

    @type bookTitle: C{string}
    @param bookTitle: Title for the book.

    @rtype: C{bool}
    @return: Returns true or false
    """

    url_title = bookiSlugify(bookTitle)

    if url_title == '':
        return False

    try:
        book = models.Book.objects.get(Q(title=bookTitle) | Q(url_title = url_title))
    except models.Book.DoesNotExist:
        return True

    return False


def createBook(user, bookTitle, status = "new", bookURL = None):
    """
    Creates book.

    @todo: Do something about status.

    @type user: C{django.contrib.auth.models.User}
    @param user: Booki user who will be book owner
    @type bookTitle: C{string}
    @param bookTitle: Title for the book. If bookURL is omitted it will slugify title for the url version
    @type status: C{string} 
    @param status: String name for the status (optional)
    @type bookURL: C{string}
    @param bookURL: URL title for the book (optional)

    @rtype: C{booki.editor.models.Book}
    @return: Returns book object
    """

    if bookURL:
        url_title = bookURL
    else:
        url_title = bookiSlugify(bookTitle)

    book = models.Book(url_title = url_title,
                       title = bookTitle,
                       owner = user, 
                       published = datetime.datetime.now())

    book.save()

    # put this in settings file
    status_default = ["new", "needs content", "completed", "to be proofed"]
    n = len(status_default)

    for statusName in status_default:
        status = models.BookStatus(book=book, name=statusName, weight=n)
        status.save()
        n -= 1

    # not use "not published" but first in the list maybe, or just status
    book.status = models.BookStatus.objects.get(book=book, name="new")
    book.save()
    
    
    version = models.BookVersion(book = book,
                                 major = 1,
                                 minor = 0,
                                 name = 'initial',
                                 description = '')
    version.save()

    book.version = version
    book.save()

    logBookHistory(book = book, 
                   version = version,
                   user = user,
                   kind = 'book_create')

    import booki.editor.signals    
    booki.editor.signals.book_created.send(sender = user, book = book)

    return book


class BookiGroupExist(Exception):
    def __init__(self, groupName):
        self.groupName = groupName

    def __str__(self):
        return 'Booki group already exists'

def createBookiGroup(groupName, groupDescription, owner):
    """
    Create Booki Group.

    @type groupName: C{string}
    @param groupName: Group name
    @type groupDescription: C{string}
    @param groupDescription: Group name
    @type owner: C{django.contrib.auth.models.User}
    @param owner: Group owner

    @rtype: C{booki.editor.models.BookiGroup}
    @return: Returns group object
    """

    import datetime

    try:
        bg = models.BookiGroup.objects.get(url_name = bookiSlugify(groupName))
    except models.BookiGroup.MultipleObjectsReturned:
        raise BookiGroupExist(groupName)
    except models.BookiGroup.DoesNotExist:
        group = models.BookiGroup(name = groupName,
                                  url_name = bookiSlugify(groupName),
                                  description = groupDescription,
                                  owner = owner,
                                  created = datetime.datetime.now())
        group.save()

        return group

    raise BookiGroupExist(groupName)

def checkGroupAvailability(groupName):
    """
    Checks if the group name is available or not.

    @type bookName: C{string}
    @param bookName: Name of the group.

    @rtype: C{bool}
    @return: Returns true or false
    """

    url_name = bookiSlugify(groupName)

    if url_name == '':
        return False

    try:
        group = models.BookiGroup.objects.get(Q(name=groupName) | Q(url_name = url_name))
    except models.BookiGroup.DoesNotExist:
        return True

    return False


    
