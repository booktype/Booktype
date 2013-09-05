# This file is part of Booktype.
# Copyright (c) 2013 Borko Jandras <borko.jandras@sourcefabric.org>
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
import pprint
import urllib
import logging
import hashlib
import urlparse
import datetime
import StringIO
import tempfile

from lxml import etree

import ebooklib
import ebooklib.epub
import ebooklib.utils

from django.utils.timezone import utc
from django.core.files import File
from django.core.files.base import ContentFile

from booki.editor import models
from booki.utils.misc import bookiSlugify

from ..utils import convert_file_name
from .readerplugins import TidyPlugin, ImportPlugin
from .cover import get_cover_image


logger = logging.getLogger("booktype.importer.epub")


def import_epub(epub_file, book):
    """
    Imports the EPUB book.
    """
    if isinstance(epub_file, file):
        # file on disk
        _do_import_file(epub_file.name, book)
    elif isinstance(epub_file, str) or isinstance(epub_file, unicode):
        # path to file on disk
        _do_import_file(epub_file, book)
    elif isinstance(epub_file, object):
        # some file-like object

        temp_file = tempfile.NamedTemporaryFile(prefix="booktype-", suffix=".epub", delete=False)
        for chunk in epub_file:
            temp_file.write(chunk)
        temp_file.close()

        _do_import_file(temp_file.name, book)

        os.remove(temp_file.name)


def _do_import_file(file_path, book):
    reader_options = {
        'plugins': [TidyPlugin(), ImportPlugin()]
    }

    epub_reader = ebooklib.epub.EpubReader(file_path, options=reader_options)

    epub_book = epub_reader.load()
    epub_reader.process()

    _do_import_book(epub_book, book)


def _do_import_book(epub_book, book):
    pp = pprint.PrettyPrinter(indent=4)

    chapters = {}
    toc = []

    def _parse_toc(elements):
        for _elem in elements:
            if isinstance(_elem, tuple):
                toc.append((1, _elem[0].title))
                _parse_toc(_elem[1])
            elif isinstance(_elem, ebooklib.epub.Section):
                pass
            elif isinstance(_elem, ebooklib.epub.Link):
                _u = urlparse.urlparse(_elem.href)
                _name = urllib.unquote(os.path.basename(_u.path))

                if not _name in chapters:
                    chapters[_name] = _elem.title
                    toc.append((0, _name))

    _parse_toc(epub_book.toc)

    pp.pprint(toc)

    title = epub_book.title

    now = datetime.datetime.utcnow().replace(tzinfo=utc)

    stat = models.BookStatus.objects.filter(book=book, name="new")[0]

    cover_image = get_cover_image(epub_book)
    if cover_image:
        _set_cover(book, cover_image)

    for attach in epub_book.get_items_of_type(ebooklib.ITEM_IMAGE):
        if attach == cover_image:
            continue

        att = models.Attachment(book = book,
                                version = book.version,
                                status = stat)

        s = attach.get_content()
        f = StringIO.StringIO(s)
        f2 = File(f)
        f2.size = len(s)
        att.attachment.save(attach.file_name, f2, save=False)
        att.save()
        f.close()

    _imported = {}

    for chap in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Nav and Cover are not imported
        if not chap.is_chapter():
             continue

        # check if this chapter name already exists
        name = urllib.unquote(os.path.basename(chap.file_name))
        content = chap.get_body_content()

        # maybe this part has to go to the plugin
        # but you can not get title from <title>
        if chapters.has_key(name):
            name = chapters[name]
        else:
            name = convert_file_name(name)

            if name.rfind('.') != -1:
                name = name[:name.rfind('.')]

            name = name.replace('.', '')

        chapter = models.Chapter(book = book,
                                 version = book.version,
                                 url_title = bookiSlugify(name),
                                 title = name,
                                 status = stat,
                                 content = content,
                                 created = now,
                                 modified = now)

        chapter.save()
        _imported[urllib.unquote(os.path.basename(chap.file_name))] = chapter

    # fix links
    for chap in  epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if not chap.is_chapter():
             continue

        content = chap.get_content()

        try:
            tree = ebooklib.utils.parse_html_string(content)
        except:
            pass

        body = tree.find('body')

        if body is not None:
            to_save = False

            for _item in body.iter():
                if _item.tag == 'a':
                    _href = _item.get('href')

                    if _href:
                        _u = urlparse.urlparse(_href)
                        pth = urllib.unquote(os.path.basename(_u.path))

                        if pth in _imported:
                            _name = _imported[pth].url_title

                            _u2 = urlparse.urljoin(_href, '../'+_name+'/')
                            _item.set('href', _u2)
                            to_save = True

            if to_save:
                chap.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
                _imported[urllib.unquote(os.path.basename(chap.file_name))].content = chap.content
                _imported[urllib.unquote(os.path.basename(chap.file_name))].save()

    n = len(toc)+1

    for _elem in toc:
        if _elem[0] == 1: #section
            c = models.BookToc(book = book,
                               version = book.version,
                               name = _elem[1],
                               chapter = None,
                               weight = n,
                               typeof = 2)
            c.save()
        else:
            if not _elem[1] in _imported:
                continue

            chap = _imported[_elem[1]]
            c = models.BookToc(book = book,
                               version = book.version,
                               name = chap.title,
                               chapter = chap,
                               weight = n,
                               typeof = 1)
            c.save()

        n -= 1

    # done


def _set_cover(book, cover_image):
    """ Assigns the specified cover.
    """
    cover_file = ContentFile(cover_image.get_content())
    file_name  = os.path.basename(cover_image.file_name)
    created    = datetime.datetime.now()
    title      = ''

    h = hashlib.sha1()
    h.update(cover_image.file_name)
    h.update(title)
    h.update(str(created))

    cover = models.BookCover(book = book,
                             user = book.owner,
                             cid = h.hexdigest(),
                             title = title,
                             filename = file_name[:250],
                             width = 0,
                             height = 0,
                             approved = False,
                             is_book = False,
                             is_ebook = True,
                             is_pdf = False,
                             created = created)
    cover.save()

    cover.attachment.save(file_name, cover_file, save = False)
    cover.save()


__all__ = (
    "import_epub",
)
