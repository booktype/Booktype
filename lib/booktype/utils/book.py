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
import os
import shutil
import logging

from django.db.models import Q
from django.conf import settings

import booki.editor.signals
from booki.editor import models
from booki.utils.log import logBookHistory
from booktype.utils import config
from .misc import booktype_slugify, get_default_book_status

try:
    from PIL import Image
except ImportError:
    import Image


logger = logging.getLogger('booktype.utils.book')


def check_book_availability(book_title):
    """
    Checks if the book name is available or not.

    @type book_title: C{string}
    @param book_title: Title for the book.

    @rtype: C{bool}
    @return: Returns true or false
    """

    url_title = booktype_slugify(book_title[:100])

    if url_title == '':
        return False

    try:
        models.Book.objects.get(Q(title=book_title) | Q(url_title=url_title))
    except models.Book.DoesNotExist:
        return True

    return False


def create_book(user, book_title, status=None, book_url=None):
    """
    Creates book.

    @type user: C{django.contrib.auth.models.User}
    @param user: Booktype user who will be book owner
    @type book_title: C{string}
    @param book_title: Title for the book. If book_url is omitted it will slugify title for the url version
    @type status: C{string}
    @param status: String name for the status (optional)
    @type book_url: C{string}
    @param book_url: URL title for the book (optional)

    @rtype: C{booki.editor.models.Book}
    @return: Returns book object
    """

    if book_url:
        url_title = book_url[:100]
    else:
        url_title = booktype_slugify(book_title[:100])

    book = models.Book(
        url_title=url_title,
        title=book_title,
        owner=user,
        created=datetime.datetime.now(),
        published=datetime.datetime.now(),
        hidden=False,
        description='',
        cover=None
    )
    book.save()

    status_list = config.get_configuration('CHAPTER_STATUS_LIST')
    n = len(status_list)

    default_status = status if status else get_default_book_status()

    for status_elem in status_list:
        status = models.BookStatus(
            book=book, name=status_elem['name'],
            weight=n, color=status_elem['color']
        )
        status.save()
        n -= 1

    # not use "not published" but first in the list maybe, or just status
    book.status = models.BookStatus.objects.get(book=book, name=default_status)
    book.save()

    track_changes = config.get_configuration('BOOK_TRACK_CHANGES', False)
    version = models.BookVersion(
        book=book,
        major=1,
        minor=0,
        name='initial',
        description='',
        created=datetime.datetime.now(),
        track_changes=track_changes
    )
    version.save()

    book.version = version
    book.save()

    logBookHistory(
        book=book,
        version=version,
        user=user,
        kind='book_create'
    )
    booki.editor.signals.book_created.send(sender=user, book=book)
    return book


class BooktypeGroupExist(Exception):
    def __init__(self, group_name):
        self.group_name = group_name

    def __str__(self):
        return 'Booktype group already exists'


def create_booktype_group(group_name, group_description, owner):
    """
    Create Booktype Group.

    @type group_name: C{string}
    @param group_name: Group name
    @type group_description: C{string}
    @param group_description: Group description
    @type owner: C{django.contrib.auth.models.User}
    @param owner: Group owner

    @rtype: C{booki.editor.models.BookiGroup}
    @return: Returns group object
    """

    try:
        models.BookiGroup.objects.get(url_name=booktype_slugify(group_name))
    except models.BookiGroup.MultipleObjectsReturned:
        raise BooktypeGroupExist(group_name)
    except models.BookiGroup.DoesNotExist:
        group = models.BookiGroup(name=group_name,
                                  url_name=booktype_slugify(group_name),
                                  description=group_description,
                                  owner=owner,
                                  created=datetime.datetime.now())
        group.save()

        return group

    raise BooktypeGroupExist(group_name)


def check_group_availability(group_name):
    """
    Checks if the group name is available or not.

    @type book_name: C{string}
    @param book_name: Name of the group.

    @rtype: C{bool}
    @return: Returns true or false
    """

    url_name = booktype_slugify(group_name)

    if url_name == '':
        return False

    try:
        models.BookiGroup.objects.get(Q(name=group_name) | Q(url_name=url_name))
    except models.BookiGroup.DoesNotExist:
        return True

    return False


def set_book_cover(book, file_name):
    """
    Creates thumbnail image from uploaded file

    @type book; C{booki.editor.models.Book}
    @param: Book object

    @type file_name: C{UploadedFile}
    @param: Image file
    """

    try:
        im = Image.open(file_name)
        im.thumbnail((240, 240), Image.ANTIALIAS)

        dir_path = os.path.join(settings.MEDIA_ROOT, settings.COVER_IMAGE_UPLOAD_DIR)
        file_path = os.path.join(dir_path, '{}.jpg'.format(book.id))

        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

        im.save(file_path, "JPEG")

        # If we have used book.cover.save we would end up with obsolete files  on disk
        book.cover = '%s%s.jpg' % (settings.COVER_IMAGE_UPLOAD_DIR, book.id)
    except Exception, e:
        logger.exception(e)


def rename_book(book, new_title, new_url_title):
    """
    Rename the Book. This function will also rename the path for Attachments.

    @type book; C{booki.editor.models.Book}
    @param: Book object

    @type new_title: C{string}
    @param: New book title

    @type new_url_title: C{string}
    @param: New URL title
    """

    try:
        os.rename(
            '{0}/books/{1}'.format(settings.DATA_ROOT, book.url_title),
            '{0}/books/{1}'.format(settings.DATA_ROOT, new_url_title)
        )
    except OSError as ex:
        logger.error("ERROR [{0}]: {1} {2}".format(ex.errno, ex.strerror, ex.filename))

    try:
        os.rename(
            '{0}/styles/{1}'.format(settings.DATA_ROOT, book.url_title),
            '{0}/styles/{1}'.format(settings.DATA_ROOT, new_url_title)
        )
    except OSError as ex:
        logger.error("ERROR [{0}]: {1} {2}".format(ex.errno, ex.strerror, ex.filename))

    book.title = new_title
    book.url_title = new_url_title

    n = len(settings.DATA_ROOT) + len('books/') + 1

    # This entire thing with full path in attachments is silly and kind of legacy problem from early versions of
    # Django. This should be fixed in the future.

    for attachment in models.Attachment.objects.filter(version__book=book):
        name = attachment.attachment.name

        if name.startswith('/'):
            j = name[n:].find('/')
            newName = '%s/books/%s%s' % (settings.DATA_ROOT, book.url_title, name[n:][j:])

            attachment.attachment.name = newName
            attachment.save()

    return True


def remove_book(book):
    """
    Remove the Book.

    @type book; C{booki.editor.models.Book}
    @param: Book object
    """

    book_URL_title = book.url_title
    book_ID = book.id

    # delete the book
    book.delete()

    # remove attachments directory
    book_path = '%s/books/%s' % (settings.DATA_ROOT, book_URL_title)

    if os.path.isdir(book_path):
        try:
            shutil.rmtree(book_path)
        except OSError:
            # ignore errors for now
            pass

    # remove cover image
    try:
        os.remove('%s/%s%s.jpg' % (settings.MEDIA_ROOT, settings.COVER_IMAGE_UPLOAD_DIR, book_ID))
    except OSError:
        # ignore errors for now
        pass

    return True
