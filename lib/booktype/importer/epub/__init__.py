import os
import pprint
import urllib
import logging
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

from booki.editor import models
from booki.utils.misc import bookiSlugify

from ..utils import convert_file_name
from .readerplugins import TidyPlugin, ImportPlugin


logger = logging.getLogger("booktype.importer.epub")


def import_file_to_book(uploaded_epub_file, book):
    epub_file = tempfile.NamedTemporaryFile(prefix="jaspers-", suffix=".epub", delete=False)
    epub_file_name = epub_file.name

    for chunk in uploaded_epub_file.chunks():
        epub_file.write(chunk)

    epub_file.close()

    reader_options = {
        'plugins': [TidyPlugin(), ImportPlugin()]
    }

    epub_reader = ebooklib.epub.EpubReader(epub_file_name, options=reader_options)

    epub_book = epub_reader.load()
    epub_reader.process()

    _do_import(epub_book, book)

    os.remove(epub_file_name)


def _do_import(epub_book, book):
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

    for attach in epub_book.get_items_of_type(ebooklib.ITEM_IMAGE):
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


__all__ = (
    "import_file_to_book",
)
