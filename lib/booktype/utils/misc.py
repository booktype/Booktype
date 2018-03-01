# This file is part of Booktype.
# Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import os
import urllib
import config
import logging
import urlparse
import tempfile
import ebooklib
import datetime
import StringIO
import importlib

from django.conf import settings
from django.core.files import File
from django.core.validators import validate_email
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from lxml import etree
from ebooklib import epub
from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string

from booki.editor import models
from .tidy import tidy_cleanup

try:
    from PIL import Image
except ImportError:
    import Image

logger = logging.getLogger("booktype.utils.misc")


class TidyPlugin(BasePlugin):
    NAME = 'Tidy HTML'
    OPTIONS = {
        'indent': 'yes',
        'tidy-mark': 'no',
        'drop-font-tags': 'no',
        'uppercase-attributes': 'no',
        'uppercase-tags': 'no'
    }

    def __init__(self, extra={}):
        self.options = dict(self.OPTIONS)
        self.options.update(extra)

    def html_after_read(self, book, chapter):
        if not chapter.content:
            return None

        _, content = tidy_cleanup(chapter.get_content(), **self.options)
        return content

    def html_before_write(self, book, chapter):
        if not chapter.content:
            return None

        _, content = tidy_cleanup(chapter.get_content(), **self.options)
        return content


class ImportPlugin(BasePlugin):
    NAME = 'Import Plugin'

    def __init__(self, remove_attributes=None):
        if remove_attributes:
            self.remove_attributes = remove_attributes
        else:
            # different kind of onmouse
            self.remove_attributes = ['class', 'style', 'id', 'onkeydown', 'onkeypress', 'onkeyup',
                                      'onclick', 'ondblclik', 'ondrag', 'ondragend', 'ondragenter',
                                      'ondragleave', 'ondragover', 'ondragstart', 'ondrop',
                                      'onmousedown', 'onmousemove', 'onmouseout', 'onmouseover',
                                      'onmouseup', 'onmousewheel', 'onscroll']

    def after_read(self, book):
        # change all the file names for images
        #   - should fix if attachment name has non ascii characters in the name
        #   - should remove the space if file name has it inside

        for att in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            att.file_name = _convert_file_name(att.file_name)

    def html_after_read(self, book, chapter):
        try:
            tree = parse_html_string(chapter.content)
        except:
            return

        root = tree.getroottree()

        if len(root.find('head')) != 0:
            head = tree.find('head')
            title = head.find('title')

            if title is not None:
                chapter.title = title.text

        if len(root.find('body')) != 0:
            body = tree.find('body')

            # todo:
            # - fix <a href="">
            # - fix ....

            for _item in body.iter():
                if _item.tag == 'img':
                    _name = _item.get('src')
                    # this is not a good check
                    if _name and not _name.lower().startswith('http'):
                        _item.set('src', 'static/%s' % _convert_file_name(_name))

                for t in self.remove_attributes:
                    if t in _item.attrib:
                        del _item.attrib[t]

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)


class LoadPlugin(BasePlugin):
    NAME = 'Load Plugin'

    def after_read(self, book):

        # change all the file names for images
        for att in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            att.file_name = os.path.basename(att.file_name)

    def html_after_read(self, book, chapter):
        if not chapter.is_chapter():
            return

        try:
            tree = parse_html_string(chapter.content)
        except:
            return

        root = tree.getroottree()

        if len(root.find('head')) != 0:
            head = tree.find('head')
            title = head.find('title')

            if title is not None:
                chapter.title = title.text

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)


def remove_unknown_tags(html_content):
    """
    Remove unknown tags from a given html content string.
    This method is based on a method of Cleaner class on lxml.html module
    """

    from lxml.html import defs

    try:
        tree = parse_html_string(html_content.encode('utf-8'))
    except Exception as err:
        logger.error(
            "ERROR RemoveUnknownTags: Problem while trying to parse content. Returning raw content. Msg: %s" % err)
        return html_content

    allow_tags = set(defs.tags)

    if allow_tags:
        bad = []
        for el in tree.iter():
            if el.tag not in allow_tags:
                bad.append(el)
        if bad:
            if bad[0] is tree:
                el = bad.pop(0)
                el.tag = 'div'
                el.attrib.clear()
            for el in bad:
                el.drop_tag()

    return etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)


def _convert_file_name(file_name):

    name = os.path.basename(file_name)
    if name.rfind('.') != -1:
        _np = name[:name.rfind('.')]
        _ext = name[name.rfind('.'):]
        name = booktype_slugify(_np) + _ext

    name = urllib.unquote(name)
    name = name.replace(' ', '_')

    return name


def import_from_string(import_name):
    """
    Imports a class object from a given dotted string.

    :Args:
        - import_name: String in dotted notation of the class to be imported.

    :Returns:
        The imported class
    """

    try:
        if '.' in import_name:
            module_str, klass = import_name.rsplit('.', 1)
            module = importlib.import_module(module_str)
            return getattr(module, klass)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError) as err:
        raise err


# THIS IS TEMPORARY PLACE AND TEMPORARY CODE
def import_book_from_file(epub_file, user, **kwargs):
    import uuid

    from django.utils.timezone import utc
    from lxml import etree
    from ebooklib.utils import parse_html_string
    from .book import create_book

    opts = {'plugins': [TidyPlugin(), ImportPlugin()]}
    epub_book = epub.read_epub(epub_file, opts)

    chapters = {}
    toc = []

    def _parse_toc(elements, parent=None):
        for _elem in elements:
            # used later to get parent of an elem
            unique_id = uuid.uuid4().hex

            if isinstance(_elem, tuple):
                toc.append((1, _elem[0].title, unique_id, parent))
                _parse_toc(_elem[1], unique_id)
            elif isinstance(_elem, epub.Section):
                pass
            elif isinstance(_elem, epub.Link):
                _u = urlparse.urlparse(_elem.href)
                _name = urllib.unquote(os.path.basename(_u.path))
                if not _name:
                    _name = _elem.title

                if _name not in chapters:
                    chapters[_name] = _elem.title
                    toc.append((0, _name, unique_id, parent))

    _parse_toc(epub_book.toc)

    epub_book_name = epub_book.metadata[epub.NAMESPACES['DC']]['title'][0][0]
    title = kwargs.get('book_title', epub_book_name)
    book_url = kwargs.get('book_url', None)

    # must check if title already exists
    book = create_book(user, title, book_url=book_url)
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    stat = models.BookStatus.objects.filter(book=book, name="new")[0]

    for attach in epub_book.get_items_of_type(ebooklib.ITEM_IMAGE):
        att = models.Attachment(
            book=book,
            version=book.version,
            status=stat
        )

        s = attach.get_content()
        f = StringIO.StringIO(s)
        f2 = File(f)
        f2.size = len(s)
        att.attachment.save(attach.file_name, f2, save=False)
        att.save()
        f.close()

    _imported = {}
    # TODO: ask about importing empty sections

    for chap in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Nav and Cover are not imported
        if not chap.is_chapter():
            continue

        # check if this chapter name already exists
        name = urllib.unquote(os.path.basename(chap.file_name))
        content = chap.get_body_content()

        # maybe this part has to go to the plugin
        # but you can not get title from <title>
        if name in chapters:
            name = chapters[name]
        else:
            name = _convert_file_name(name)
            if name.rfind('.') != -1:
                name = name[:name.rfind('.')]
            name = name.replace('.', '')

        chapter = models.Chapter(
            book=book,
            version=book.version,
            url_title=booktype_slugify(unicode(name)),
            title=name,
            status=stat,
            content=content,
            created=now,
            modified=now
        )
        chapter.save()
        _imported[urllib.unquote(os.path.basename(chap.file_name))] = chapter

    # fix links
    for chap in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if not chap.is_chapter():
            continue

        content = chap.get_content()
        try:
            tree = parse_html_string(content)
        except:
            pass

        root = tree.getroottree()

        if len(root.find('body')) != 0:
            body = tree.find('body')

            to_save = False

            for _item in body.iter():
                if _item.tag == 'a':
                    _href = _item.get('href')

                    if _href:
                        _u = urlparse.urlparse(_href)
                        pth = urllib.unquote(os.path.basename(_u.path))

                        if pth in _imported:
                            _name = _imported[pth].url_title

                            _u2 = urlparse.urljoin(_href, '../' + _name + '/')
                            _item.set('href', _u2)
                            to_save = True

            if to_save:
                chap.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
                _imported[urllib.unquote(os.path.basename(chap.file_name))].content = chap.content
                _imported[urllib.unquote(os.path.basename(chap.file_name))].save()

    n = len(toc) + 1
    parents = {}

    for _elem in toc:
        if _elem[0] == 1:  # section
            toc_item = models.BookToc(
                book=book,
                version=book.version,
                name=_elem[1],
                chapter=None,
                weight=n,
                typeof=2
            )
        else:
            if not _elem[1] in _imported:
                continue

            chap = _imported[_elem[1]]
            toc_item = models.BookToc(
                book=book,
                version=book.version,
                name=chap.title,
                chapter=chap,
                weight=n,
                typeof=1
            )

        # check if elem has parent
        if _elem[3]:
            toc_item.parent = parents.get(_elem[3], None)
        toc_item.save()

        # decrease weight
        n -= 1

        # save temporarily the toc_item in parent
        parents[_elem[2]] = toc_item

    return book


def set_group_image(groupid, file_object, x_size, y_size):
    """
    Creates thumbnail image from uploaded file

    @type groupid; C{booki.editor.models.BookiGroup}
    @param: Group object

    @type file_object: C{UploadedFile}
    @param: Image file
    """

    try:
        GROUP_IMAGE_UPLOAD_DIR = settings.GROUP_IMAGE_UPLOAD_DIR
    except AttributeError:
        GROUP_IMAGE_UPLOAD_DIR = 'group_images/'

    fh, fname = save_uploaded_as_file(file_object)
    try:
        im = Image.open(fname)
        im.thumbnail((x_size, y_size), Image.ANTIALIAS)
        new_path = os.path.join(settings.MEDIA_ROOT, GROUP_IMAGE_UPLOAD_DIR)

        if not os.path.exists(new_path):
            os.mkdir(new_path)

        file_name = '{}.jpg'.format(os.path.join(new_path, str(groupid)))
        im.save(file_name, "JPEG")
    except:
        file_name = ''

    os.unlink(fname)

    return file_name


def booktype_slugify(text):
    """
    Wrapper for default Django function. Default function does not work with unicode strings.

    @type text: C{string}
    @param: Text you want to slugify

    @rtype: C{string}
    @return: Returns slugified text
    """

    try:
        import unidecode

        text = unidecode.unidecode(text)
    except ImportError:
        pass

    return slugify(text)


def create_thumbnail(fname, size=(100, 100), aspect_ratio=False):
    """

    @type fname: C{string}
    @param: Full path to image file
    @type size: C{tuple}
    @param: Width and height of the thumbnail

    @rtype: C{Image}
    @return: Returns PIL Image object
    """

    im = Image.open(fname)
    width, height = im.size

    if width > height:
        delta = width - height
        left = int(delta / 2)
        upper = 0
        right = height + left
        lower = height
    else:
        delta = height - width
        left = 0
        upper = int(delta / 2)
        right = width
        lower = width + upper

    if not aspect_ratio:
        im = im.crop((left, upper, right, lower))

    im.thumbnail(size, Image.ANTIALIAS)

    return im


def save_uploaded_as_file(file_object):
    """
    Saves uploaded_file into file on disk.

    @type file_object: C{uploaded_file}
    @param: Image file

    @rtype: C{Tuple}
    @return: Retursns file handler and file name as tuple
    """

    fh, fname = tempfile.mkstemp(suffix='', prefix='profile')

    f = open(fname, 'wb')

    for chunk in file_object.chunks():
        f.write(chunk)

    f.close()

    return (fh, fname)


def set_profile_image(user, file_object):
    """
    Creates thumbnail image from uploaded file and saves it as profile image.

    @type user; C{django.contrib.auth.models.User}
    @param: Booktype user

    @type file_object: C{uploaded_file}
    @param: Image file
    """

    fh, fname = save_uploaded_as_file(file_object)

    try:
        im = create_thumbnail(fname, size=(100, 100))

        dir_path = os.path.join(settings.MEDIA_ROOT, settings.PROFILE_IMAGE_UPLOAD_DIR)
        file_path = os.path.join(dir_path, '{}.jpg'.format(user.username))

        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

        im.save(file_path, 'JPEG')

        # If we would use just profile.image.save method then out files would just end up with _1, _2, ... postfixes

        profile = user.profile
        profile.image = '%s%s.jpg' % (settings.PROFILE_IMAGE_UPLOAD_DIR, user.username)
        profile.save()
    except:
        pass

    os.unlink(fname)


def get_directory_size(dir_path):
    """
    Returns total file size of all files in this directory and subdirectories.

    @type dir_path; C{string}
    @param: Directory path

    @rtype text: C{int}
    @param: Returns total size of all files in subdirectories
    """

    total_size = 0

    for dirpath, dirnames, filenames in os.walk(dir_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    return total_size


def is_user_limit_reached():
    """
    Checks if maximum number of user is reached.

    @rtype text: C{book}
    @param: Returns True if maximum number of users is reached
    """

    max_users = config.get_configuration('BOOKTYPE_MAX_USERS')

    if not isinstance(max_users, int):
        # We should show some kind of warning here
        return False

    # 0 means unlimited and that is the default value
    if max_users == 0:
        return False

    # get list of all active accounts
    num_users = User.objects.filter(is_active=True).count()

    if num_users >= max_users:
        return True

    return False


def is_book_limit_reached():
    """
    Checks if maximum number of books is reaced.

    @rtype text: C{book}
    @param: Returns True if maximum number of books is reached
    """

    max_books = config.get_configuration('BOOKTYPE_MAX_BOOKS')

    if not isinstance(max_books, int):
        # We should show some kind of warning here
        return False

    # 0 means unlimited and that is the default value
    if max_books == 0:
        return False

    # get list of all active books
    num_books = models.Book.objects.all().count()

    if num_books >= max_books:
        return True

    return False


def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

    return False


def get_default_book_status():
    """Returns the default book status"""

    status_list = config.get_configuration('CHAPTER_STATUS_LIST')
    default_status = config.get_configuration('CHAPTER_STATUS_DEFAULT', status_list[0]['name'])
    return default_status


def get_available_themes():
    """
    get sorted themes name from the themes fodler
    :return: list of themes names sorted by name
    """
    try:
        available_themes = os.listdir(os.path.join(settings.BOOKTYPE_ROOT, 'themes'))
        available_themes.sort()
    except OSError as e:
        logger.error('Error during checking theme availability: {0}'.format(e))
        raise e

    return available_themes


def get_file_extension(filename):
    """
    Extract extension for a given filename

    Keyword arguments:
        filename -- String with the name of the file

    Returns:
        Extension name string of the file
    """

    _, ext = os.path.splitext(os.path.basename(filename.lower()))
    return ext[1:]


def has_book_limit(user):
    """
    Checks if user reached book limit.

    @rtype text: C{user}
    @param: Returns True if user reached book limit
    """
    if not user.is_authenticated():
        return True

    if user.is_superuser:
        return False

    book_limit = config.get_configuration('BOOKTYPE_BOOKS_PER_USER')['limit_global']

    user_limit = filter(
        lambda item: item['username'] == user.username,
        config.get_configuration('BOOKTYPE_BOOKS_PER_USER')['limit_by_user']
    )

    if user_limit:
        book_limit = user_limit[0]['limit']

    return models.Book.objects.filter(owner=user).count() >= book_limit != -1

