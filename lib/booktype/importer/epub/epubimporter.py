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
import difflib
import logging
import hashlib
import urlparse
import datetime

import lxml.html
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
from ..notifier import Notifier
from ..delegate import Delegate
from .readerplugins import TidyPlugin, ImportPlugin
from .cover import get_cover_image, is_valid_cover


logger = logging.getLogger("booktype.importer.epub")


__all__ = ("EpubImporter", )


class EpubImporter(object):

    def __init__(self):
        self.notifier = Notifier() # null notifier
        self.delegate = Delegate() # null delegate


    def import_file(self, file_path, book):
        reader_plugins  = [TidyPlugin(), ImportPlugin()]
        reader_plugins += self.delegate.get_reader_plugins()

        reader_options = {
            'plugins': reader_plugins,
        }

        epub_reader = ebooklib.epub.EpubReader(file_path, options=reader_options)

        epub_book = epub_reader.load()
        epub_reader.process()

        self._import_book(epub_book, book)


    def _import_book(self, epub_book, book):
        titles = {}
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

                    if not _name in titles:
                        titles[_name] = _elem.title
                        toc.append((0, _name))

        _parse_toc(epub_book.toc)
        self.notifier.debug("TOC structure: \n{}".format(pprint.pformat(toc, indent=4)))

        now = datetime.datetime.utcnow().replace(tzinfo=utc)

        stat = models.BookStatus.objects.filter(book=book, name="new")[0]

        # assign cover image if there is one
        #
        cover_image = get_cover_image(epub_book)
        if cover_image:
            self._set_cover(book, cover_image)

        # import all images in the EPUB
        #
        for image in epub_book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if image == cover_image:
                continue

            if not self.delegate.should_import_image(image):
                continue

            att = models.Attachment(book = book,
                                    version = book.version,
                                    status = stat)

            with ContentFile(image.get_content()) as content_file:
                att.attachment.save(image.file_name, content_file, save=False)
                att.save()

            self.notifier.debug("Imported image: {} -> {}".format(image, att))

        # Chapter objects indexed by document file name
        chapters = {}

        # import all document items from the EPUB
        #
        for document in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # Nav and Cover are not imported
            if not document.is_chapter():
                continue

            if not self.delegate.should_import_document(document):
                continue

            name = urllib.unquote(os.path.basename(document.file_name))
            title = ''

            # maybe this part has to go to the plugin
            # but you can not get title from <title>
            if titles.has_key(name):
                title = titles[name]
            else:
                title = convert_file_name(name)

                if title.rfind('.') != -1:
                    title = title[:name.rfind('.')]

                title = title.replace('.', '')

            # TODO: check if this chapter title already exists

            content = self._create_content(document, title)

            chapter = models.Chapter(book = book,
                                     version = book.version,
                                     url_title = bookiSlugify(title),
                                     title = title,
                                     status = stat,
                                     content = content,
                                     created = now,
                                     modified = now)
            chapter.save()

            chapters[name] = chapter

            self.notifier.debug("Imported chapter: {} -> {}".format(document, chapter))

        # fix links to chapters
        #
        for chapter in chapters.itervalues():
            self._fix_links(chapter, chapters)

        # create TOC objects
        self._make_toc(book, toc, chapters)

        # done


    def _create_content(self, document, title):
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')

        content = document.get_body_content()

        tree = lxml.html.fragment_fromstring(content, create_parent=True, parser=lxml.html.HTMLParser(encoding='utf-8'))

        heading = self._find_heading(tree, title)

        if heading:
            if heading.tag != 'h1':
                heading.tag = 'h1' # promote to h1
        else:
            self._demote_headings(tree)

            heading = etree.Element('h1')
            heading.text = title

            tree.insert(0, heading)
            heading.tail = tree.text
            tree.text = ''


        tree_str = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=False)

        a = len("<div>")
        b = tree_str.rfind("</div>")
        content = tree_str[a:b]

        return content


    def _demote_headings(self, tree, n=1):
        headings = list(tree.iter('h{}'.format(n)))

        if headings and n < 5:
            self._demote_headings(tree, n+1)

        for h in headings:
            h.tag = 'h{}'.format(n+1)


    def _find_heading(self, tree, title):
        if tree.text:
            # text before heading
            return None

        heading = None

        for n in range(1, 7):
            elm = list(tree.iter('h{}'.format(n)))

            if elm:
                if len(elm) == 1:
                    # must be only one heading at this level
                    heading = elm[0]
                break

        if heading is not None:
            heading_text = unicode(etree.tostring(heading, method='text', encoding='utf-8'), 'utf-8')
            if difflib.SequenceMatcher(None, heading_text, title).ratio() > 0.9:
                return heading


    def _make_toc(self, book, toc, chapters):
        """ Creates TOC objects.
        """
        n = len(toc) + 1

        for toc_type, name in toc:
            if toc_type == 1: # section
                c = models.BookToc(book = book,
                                   version = book.version,
                                   name = name,
                                   chapter = None,
                                   weight = n,
                                   typeof = 2)
            else:
                chapter = chapters.get(name)

                if chapter is None:
                    continue

                c = models.BookToc(book = book,
                                   version = book.version,
                                   name = chapter.title,
                                   chapter = chapter,
                                   weight = n,
                                   typeof = 1)

            c.save()
            n -= 1


    def _fix_links(self, chapter, chapters):
        """ Fixes internal links so they point to chapter URLs
        """
        try:
            tree = ebooklib.utils.parse_html_string(chapter.content)
        except:
            return

        body = tree.find('body')

        if body is None:
            return

        to_save = False

        for anchor in body.iter('a'):
            href = anchor.get('href')

            if href is None:
                continue

            urlp = urlparse.urlparse(href)
            name = urllib.unquote(os.path.basename(urlp.path))

            if name in chapters:
                title = chapters[name].url_title
                fixed_href = urlparse.urljoin(href, '../{}/'.format(title))
                anchor.set('href', fixed_href)
                to_save = True

        if to_save:
            chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
            chapter.save()


    def _set_cover(self, book, cover_image):
        """ Assigns the specified cover.
        """

        is_valid, reason = is_valid_cover(cover_image)
        if not is_valid:
            self.notifier.warning("Not using {} as a cover image -- {}".format(cover_image.file_name, reason))
            return

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

        self.notifier.info("Using {} as cover image".format(file_name))
