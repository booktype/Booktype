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
import uuid
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
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

from booki.editor import models
from booktype.utils.misc import booktype_slugify

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

        # Attachment objects indexed by image file name
        self._attachments = {}
        # Chapter objects indexed by document file name
        self._chapters = {}


    def import_file(self, file_path, book):
        reader_plugins  = [TidyPlugin(), ImportPlugin()]
        reader_plugins += self.delegate.get_reader_plugins()

        reader_options = {
            'plugins': reader_plugins,
        }

        epub_reader = ebooklib.epub.EpubReader(file_path, options=reader_options)

        epub_book = epub_reader.load()
        epub_reader.process()

        self.delegate.notifier = self.notifier

        self._import_book(epub_book, book)


    def _import_book(self, epub_book, book):
        titles = {}
        toc = []

        def _parse_toc(elements, parent=None):
            for _elem in elements:
                # used later to get parent of an elem
                unique_id = uuid.uuid4().hex 

                if isinstance(_elem, tuple):
                    toc.append((1, _elem[0].title, unique_id, parent))
                    _parse_toc(_elem[1])
                elif isinstance(_elem, ebooklib.epub.Section):
                    pass
                elif isinstance(_elem, ebooklib.epub.Link):
                    _urlp = urlparse.urlparse(_elem.href)
                    _name = os.path.normpath(urllib.unquote(_urlp.path))

                    # check in case _name is an empty string
                    if not _name:
                        _name = _elem.title

                    if not _name in titles:
                        titles[_name] = _elem.title
                        toc.append((0, _name, unique_id, parent))

        _parse_toc(epub_book.toc)
        self.notifier.debug("TOC structure: \n{}".format(pprint.pformat(toc, indent=4)))

        now = datetime.datetime.utcnow().replace(tzinfo=utc)

        stat = models.BookStatus.objects.filter(book=book, name="new")[0]

        # assign cover image if there is one
        cover_image = get_cover_image(epub_book)
        if cover_image:
            self._set_cover(book, cover_image)

        # import all images in the EPUB
        for image in epub_book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if image == cover_image:
                continue

            if not self.delegate.should_import_image(image):
                continue

            name = os.path.normpath(image.file_name)

            att = models.Attachment(book = book,
                                    version = book.version,
                                    status = stat)

            with ContentFile(image.get_content()) as content_file:
                attName, attExt = os.path.splitext(os.path.basename(name))

                att.attachment.save('{}{}'.format(booktype_slugify(attName), attExt), content_file, save=False)
                att.save()

            self._attachments[name] = att

            self.notifier.debug("Imported image: {} -> {}".format(image, att))

        # URL titles assigned so far
        url_titles = []

        def _make_url_title(title, i=0):
            url_title = booktype_slugify(title)
            if i > 0:
                url_title += "_" + str(i)
            if not url_title in url_titles:
                url_titles.append(url_title)
                return url_title
            else:
                return _make_url_title(title, i+1)

        # import all document items from the EPUB
        for document in epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # Nav and Cover are not imported
            if not document.is_chapter():
                continue

            if not self.delegate.should_import_document(document):
                continue

            name = os.path.normpath(document.file_name)
            title = ''

            # maybe this part has to go to the plugin
            # but you can not get title from <title>
            if titles.has_key(name):
                title = titles[name]
            else:
                title = convert_file_name(name)

                if title.rfind('.') != -1:
                    title = title[:title.rfind('.')]

                title = title.replace('.', '')

            url_title = _make_url_title(title)
            content = self._create_content(document, title)

            chapter = models.Chapter(
                book = book,
                version = book.version,
                url_title = url_title,
                title = title,
                status = stat,
                content = content,
                created = now,
                modified = now
            )
            chapter.save()

            self._chapters[name] = chapter

            self.notifier.debug("Imported chapter: {} -> {}".format(document, chapter))

        # fix links to chapters
        for file_name, chapter in self._chapters.iteritems():
            self._fix_links(chapter, base_path=os.path.dirname(file_name))

        # create TOC objects
        self._make_toc(book, toc)

        # done


    def _create_content(self, document, title):
        if not isinstance(title, unicode):
            title = unicode(title, 'utf-8')

        content = document.get_body_content()

        tree = lxml.html.fragment_fromstring(content, create_parent=True, parser=lxml.html.HTMLParser(encoding='utf-8'))

        heading = self._find_heading(tree, title)

        if heading is not None:
            heading.getparent().remove(heading)
            del heading

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

        def matches(heading):
            heading_text = unicode(etree.tostring(heading, method='text', encoding='utf-8'), 'utf-8')
            return difflib.SequenceMatcher(None, heading_text, title).ratio() > 0.8

        def tail(heading):
            if heading.tail:
                return heading.tail.strip()

        for n in range(1, 7):
            elm = list(tree.iter('h{}'.format(n)))

            if elm:
                for heading in elm:
                    if matches(heading):
                        return heading
                    elif tail(heading):
                        # can't be in the next element
                        break
                # can't be at lower level
                break

        return None


    def _make_toc(self, book, toc):
        """ Creates TOC objects. """
        
        n = len(toc) + 1
        parents = {}

        for toc_type, name, elem_id, parent_id in toc:
            if toc_type == 1: # section
                toc_item = models.BookToc(
                    book = book,
                    version = book.version,
                    name = name,
                    chapter = None,
                    weight = n,
                    typeof = 2
                )
            else:
                chapter = self._chapters.get(name)
                if chapter is None:
                    continue

                toc_item = models.BookToc(
                    book = book,
                    version = book.version,
                    name = chapter.title,
                    chapter = chapter,
                    weight = n,
                    typeof = 1
                )

            # check if elem has parent 
            if parent_id:
                toc_item.parent = parents.get(parent_id, None)
            toc_item.save()

            # decrease weight
            n -= 1

            # save temporarily the toc_item in parent
            parents[elem_id] = toc_item


    def _fix_links(self, chapter, base_path):
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
            name = os.path.normpath(os.path.join(base_path, urllib.unquote(urlp.path)))

            if name in self._chapters:
                title = self._chapters[name].url_title
                fixed_href = urlparse.urljoin(href, '../{}/'.format(title))

                if urlp.fragment:
                    fixed_href = "{}#{}".format(fixed_href, urlp.fragment)

                anchor.set('href', fixed_href)
                to_save = True

        for image in body.iter('img'):
            src = image.get('src')

            if src is None:
                continue

            urlp = urlparse.urlparse(src)
            name = os.path.normpath(os.path.join(base_path, urllib.unquote(urlp.path)))

            if urlp.netloc:
                continue

            if name in self._attachments:
                file_name = os.path.basename(self._attachments[name].attachment.name)
                attName, attExt = os.path.splitext(file_name)

                fixed_src = urllib.quote('static/{}{}'.format(booktype_slugify(attName), attExt))
                image.set('src', fixed_src)
                to_save = True

        if to_save:
            chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
            chapter.save()


    def _set_cover(self, book, cover_image):
        """ Assigns the specified cover.
        """

        validity = self.delegate.is_valid_cover(cover_image)

        if validity is None:
            # not checked by the assigned delegate
            is_valid, reason = is_valid_cover(cover_image)
        elif isinstance(validity, bool):
            is_valid, reason = validity, None
        else:
            is_valid, reason = validity

        if not is_valid:
            if reason:
                self.notifier.warning(_("Not using {} as a cover image -- {}").format(cover_image.file_name, reason))
            else:
                self.notifier.warning(_("Not using {} as a cover image").format(cover_image.file_name))
            return

        cover_file = ContentFile(cover_image.get_content())
        file_name  = os.path.basename(cover_image.file_name)

        attName, attExt = os.path.splitext(file_name)
        file_name = '{}{}'.format(booktype_slugify(attName), attExt)

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

        self.notifier.info(_("Using {} as cover image").format(file_name))
