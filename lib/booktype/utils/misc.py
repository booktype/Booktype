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
import urlparse
import tempfile
import ebooklib

from collections import OrderedDict

from django.conf import settings
from django.template.defaultfilters import slugify
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from lxml import etree, html
from ebooklib import epub
from ebooklib.plugins import standard
from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string

from booki.editor import models

try:
    from PIL import Image
except ImportError:
    import Image


class TidyPlugin(BasePlugin):
    NAME = 'Tidy HTML'
    OPTIONS = {'tidy-mark': 'no', 'drop-font-tags': 'no', 'uppercase-attributes': 'no', 'uppercase-tags': 'no'}

    def __init__(self, extra={}):
        self.options = dict(self.OPTIONS)
        self.options.update(extra)

    def html_after_read(self, book, chapter):
        if not chapter.content:
            return None

        from .tidy import tidy_cleanup
        print chapter.file_name
        (_, chapter.content) = tidy_cleanup(chapter.get_content(), **self.options)

        return chapter.content

    def html_before_write(self, book, chapter):
        if not chapter.content:
            return None

        from .tidy import tidy_cleanup

        (_, chapter.content) = tidy_cleanup(chapter.get_content(), **self.options)

        return chapter.content


def _convert_file_name(file_name):

    name = os.path.basename(file_name)
    if name.rfind('.') != -1:
        _np = name[:name.rfind('.')]
        _ext = name[name.rfind('.'):]
        name = booktype_slugify(_np) + _ext

    name = urllib.unquote(name)
    name = name.replace(' ', '_')

    return name


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
        import os.path
        import urlparse

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
        import os.path

        # change all the file names for images
        for att in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            att.file_name = os.path.basename(att.file_name)

    def html_after_read(self, book, chapter):
        if not chapter.is_chapter():
            return

        from lxml import etree
        from ebooklib.utils import parse_html_string

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


# THIS IS TEMPORARY PLACE AND TEMPORARY CODE

def import_book_from_file(epub_file, user, **kwargs):
    import uuid
    import pprint
    import datetime
    import StringIO

    from django.utils.timezone import utc
    from django.core.files import File
    from lxml import etree
    from ebooklib.utils import parse_html_string

    from booktype.utils.book import create_book

    opts = {'plugins': [TidyPlugin(), ImportPlugin()]}
    epub_book = epub.read_epub(epub_file, opts)

    pp = pprint.PrettyPrinter(indent=4)
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
    pp.pprint(toc)

    epub_book_name = epub_book.metadata[epub.NAMESPACES['DC']]['title'][0][0]
    title = kwargs.get('book_title', epub_book_name)

    # must check if title already exists
    book = create_book(user, title)
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
            url_title=booktype_slugify(name),
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

############################################################################################################


def load_book_from_file(epub_file, user):
    from booki.editor import models

    opts = {'plugins': [LoadPlugin()]}

    epub_book = epub.read_epub(epub_file, opts)

    import pprint
    import datetime
    import StringIO
    import os.path

    pp = pprint.PrettyPrinter(indent=4)

    pp.pprint(epub_book.toc)

    from booktype.utils.book import create_book, check_book_availability

    title = epub_book.metadata[epub.NAMESPACES['DC']]['title'][0][0]
    lang = epub_book.metadata[epub.NAMESPACES['DC']]['language'][0][0]

    # must check the title
    book = create_book(user, title)

    now = datetime.datetime.now()

    stat = models.BookStatus.objects.filter(book=book, name="new")[0]

    n = 10

    from django.core.files import File

    for _item in epub_book.get_items():
        if _item.get_type() == ebooklib.ITEM_DOCUMENT and _item.is_chapter():  # CHECK IF IT IS NOT NAV
            title = _item.title
            title_url = os.path.splitext(_item.file_name)[0]

            chapter = models.Chapter(book=book,
                                     version=book.version,
                                     url_title=title_url,
                                     title=title,
                                     status=stat,
                                     content=_item.get_content(),
                                     created=now,
                                     modified=now)
            chapter.save()
        elif _item.get_type() != ebooklib.ITEM_DOCUMENT:
            att = models.Attachment(book=book,
                                    version=book.version,
                                    status=stat)

            s = _item.get_content()
            f = StringIO.StringIO(s)
            f2 = File(f)
            f2.size = len(s)
            att.attachment.save(_item.file_name, f2, save=False)
            att.save()
            f.close()

    return


def export_book(fileName, book_version):
    book = book_version.book
    epub_book = epub.EpubBook()

    # set basic info
    epub_book.set_identifier('booktype:%s' % book.url_title)
    epub_book.set_title(book.title)
    # set the language according to the language set
    epub_book.set_language('en')

    # epub_book.add_metadata(None, 'meta', '', {'name': 'booktype:owner_id', 'content': book_version.book.owner.username})

    # set description
    if book.description != '':
        epub_book.add_metadata('DC', 'description', book.description)

    # set license
    lic = book.license
    if lic:
        epub_book.add_metadata('DC', 'rights', lic.name)

    # set the author according to the owner
    epub_book.add_author(book.owner.first_name, role='aut', uid='author')

    toc = OrderedDict()
    section = []
    spine = ['nav']

    # parse and fetch only images which are inside
    embededImages = {}

    for chapter in book_version.get_toc():
        if chapter.chapter:
            c1 = epub.EpubHtml(
                title=chapter.chapter.title, 
                file_name='%s.xhtml' % (chapter.chapter.url_title, )
            )
            cont = chapter.chapter.content

            try:
                tree = parse_html_string(cont.encode('utf-8'))
            except:
                pass

            for elem in tree.iter():
                if elem.tag == 'a':
                    href = elem.get('href')
                    if href and href.startswith('../'):
                        urlp = urlparse.urlparse(href)

                        fixed_href = urlp.path[3:-1] + '.xhtml'

                        if urlp.fragment:
                            fixed_href = "{}#{}".format(fixed_href, urlp.fragment)

                        elem.set('href', fixed_href)

                if elem.tag == 'img':
                    src = elem.get('src')
                    if src:
                        elem.set('src', 'static/' + src[7:])
                        embededImages[src] = True

            c1.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)

            epub_book.add_item(c1)
            spine.append(c1)

            if chapter.parent:
                toc[chapter.parent.id][1].append(c1)
            else:
                if chapter.has_children():
                    toc[chapter.id] = [c1, []]
                else:
                    toc[chapter.id] = c1
        else:
            epub_sec = epub.Section(chapter.name)
            if chapter.parent:
                toc[chapter.parent.id][1].append(epub_sec)
            else:
                toc[chapter.id] = [epub_sec, []]

    for i, attachment in enumerate(models.Attachment.objects.filter(version=book_version)):
        if ('static/' + os.path.basename(attachment.attachment.name)) not in embededImages:
            continue

        try:
            f = open(attachment.attachment.name, "rb")
            blob = f.read()
            f.close()
        except (IOError, OSError), e:
            continue
        else:
            fn = os.path.basename(attachment.attachment.name.encode("utf-8"))
            itm = epub.EpubImage()
            itm.file_name = 'static/%s' % fn
            itm.content = blob
            epub_book.add_item(itm)

    epub_book.toc = toc.values()
    epub_book.spine = spine
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    opts = {'plugins': [TidyPlugin(), standard.SyntaxPlugin()]}
    epub.write_epub(fileName, epub_book, opts)


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

        new_path = '%s/%s' % (settings.MEDIA_ROOT, GROUP_IMAGE_UPLOAD_DIR)
        if not os.path.exists(new_path):
            os.mkdir(new_path)

        file_name = '%s/%s.jpg' % (new_path, groupid)
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


def create_thumbnail(fname, size=(100, 100)):
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
        im.save('%s/%s%s.jpg' % (settings.MEDIA_ROOT, settings.PROFILE_IMAGE_UPLOAD_DIR, user.username), 'JPEG')

        # If we would use just profile.image.save method then out files would just end up with _1, _2, ... postfixes

        profile = user.get_profile()
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