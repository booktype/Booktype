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
import logging
import urlparse
import ebooklib

from copy import deepcopy

from ..base import BaseConverter
from ..utils.epub import parse_toc_nav

from .writer import Writer
from .writerplugin import WriterPlugin
from .cover import add_cover, COVER_FILE_NAME

from .constants import (
    IMAGES_DIR, STYLES_DIR,
    DOCUMENTS_DIR, DEFAULT_LANG
)

logger = logging.getLogger("booktype.convert.epub")
TOC_TITLE = 'toc'


class EpubConverter(BaseConverter):
    name = 'epub'

    DEFAULT_STYLE = 'style1'
    css_dir = os.path.join(os.path.dirname(__file__), 'styles/')

    def convert(self, original_book, output_path):
        logger.debug('[EPUB] EpubConverter.convert')

        epub_book = ebooklib.epub.EpubBook()
        epub_book.FOLDER_NAME = 'OEBPS'

        epub_book.uid = original_book.uid
        epub_book.title = original_book.title
        epub_book.metadata = deepcopy(original_book.metadata)
        epub_book.toc = []

        logger.debug('[EPUB] Edit metadata')
        self._edit_metadata(epub_book)

        logger.debug('[EPUB] Copy items')
        self._copy_items(epub_book, original_book)

        logger.debug('[EPUB] Make navigation')
        self._make_nav(epub_book, original_book)

        logger.debug('[EPUB] Add cover')
        self._add_cover(epub_book)

        logger.debug('[EPUB] Writer plugin')

        writer_plugin = WriterPlugin()
        writer_plugin.options['style'] = self.config.get(
            'style', self.DEFAULT_STYLE)

        writer_plugin.options['lang'] = self.config.get('lang', DEFAULT_LANG)
        writer_plugin.options['preview'] = self.config.get('preview', True)

        logger.debug('[EPUB] Adding default and custom css')
        book_css = self._add_css_styles(epub_book)
        writer_plugin.options['css'] = book_css

        if self.config.get('lang', DEFAULT_LANG) == 'ar':
            rtl_css = self._rtl_style(epub_book)

            if rtl_css:
                writer_plugin.options['css'].append(rtl_css)

        writer_options = {
            'plugins': [writer_plugin, ]
        }

        logger.debug('[EPUB] Writer')
        epub_writer = Writer(
            output_path, epub_book, options=writer_options)

        logger.debug('[EPUB] Process')
        epub_writer.process()

        logger.debug('[EPUB] Write')
        epub_writer.write()

        logger.debug('[END] EPUBConverter.convert')

    def _edit_metadata(self, epub_book):
        """
        Modifies original metadata.
        """

        # delete existing 'modified' tag
        m = epub_book.metadata[ebooklib.epub.NAMESPACES["OPF"]]
        m[None] = filter(lambda (_,x): not (isinstance(x, dict) and x.get("property") == "dcterms:modified"), m[None]) # noqa

        # NOTE: probably going to extend this function in future

    def _make_nav(self, epub_book, original_book):
        """
        Creates navigational stuff (guide, ncx, nav) by copying the original.
        """

        # maps TOC items to sections and links
        self._num_of_text = 0

        def mapper(toc_item):
            add_to_guide = True

            if isinstance(toc_item[1], list):
                section_title, chapters = toc_item

                section = ebooklib.epub.Section(section_title)
                links = map(mapper, chapters)

                return (section, links)
            else:
                chapter_title, chapter_href = toc_item

                chapter_href = "{}/{}".format(DOCUMENTS_DIR, chapter_href)
                chapter_path = urlparse.urlparse(chapter_href).path

                book_item = self.items_by_path[chapter_path]
                book_item.title = chapter_title

                if self._num_of_text > 0:
                    add_to_guide = False

                self._num_of_text += 1

                if add_to_guide:
                    epub_book.guide.append({
                        'type': 'text',
                        'href': chapter_href,
                        'title': chapter_title,
                    })

                return ebooklib.epub.Link(
                    href=chapter_href, title=chapter_title, uid=book_item.id)

        # filters-out empty sections
        def _empty_sec(item):
            if isinstance(item, tuple) and len(item[1]) == 0:
                return False
            else:
                return True

        # filters-out existing cover
        def _skip_cover(item):
            if os.path.basename(item[1]) == COVER_FILE_NAME:
                return False
            return True

        toc = filter(_skip_cover, parse_toc_nav(original_book))
        toc = map(mapper, toc)
        toc = filter(_empty_sec, toc)

        epub_book.toc = toc

    def _copy_items(self, epub_book, original_book):
        """
        Populates the book by copying items from the original book
        """
        self.items_by_path = {}

        for orig_item in original_book.items:
            item = deepcopy(orig_item)
            item_type = item.get_type()
            file_name = os.path.basename(item.file_name)

            # do not copy cover
            if self._is_cover_item(item):
                continue

            if item_type == ebooklib.ITEM_IMAGE:
                item.file_name = '{}/{}'.format(IMAGES_DIR, file_name)

            elif item_type == ebooklib.ITEM_STYLE:
                item.file_name = '{}/{}'.format(STYLES_DIR, file_name)

            elif item_type == ebooklib.ITEM_DOCUMENT:
                item.file_name = '{}/{}'.format(DOCUMENTS_DIR, file_name)
                if isinstance(item, ebooklib.epub.EpubNav):
                    epub_book.spine.insert(0, item)
                    epub_book.guide.insert(0, {
                        'type': 'toc',
                        'href': item.file_name,
                        'title': self.config.get('toc_title', TOC_TITLE)
                    })
                else:
                    epub_book.spine.append(item)

            if isinstance(item, ebooklib.epub.EpubNcx):
                item = ebooklib.epub.EpubNcx()

            epub_book.add_item(item)
            self.items_by_path[item.file_name] = item

    def _add_cover(self, epub_book):
        """
        Adds cover image if present in config to the resulting EPUB
        """

        if 'cover_image' in self.config.keys():
            cover_asset = self.get_asset(self.config['cover_image'])
            add_cover(
                epub_book, cover_asset, self.config.get('lang', DEFAULT_LANG))

    def _add_css_styles(self, epub_book):
        """
        Adds default css styles and custom css text if exists in config
        """

        book_css = []

        try:
            content = open(
                '{}/default.css'.format(self.css_dir), 'rt').read()

            item = ebooklib.epub.EpubItem(
                uid='default.css',
                content=content,
                file_name='{}/{}'.format(STYLES_DIR, 'default.css'),
                media_type='text/css'
            )

            epub_book.add_item(item)
            book_css.append('default.css')
        except:
            pass

        # time to add custom css :)
        if 'css_text' in self.config.keys():
            item = ebooklib.epub.EpubItem(
                uid='custom.css',
                content=self.config.get('css_text'),
                file_name='{}/{}'.format(STYLES_DIR, 'custom.css'),
                media_type='text/css'
            )

            epub_book.add_item(item)
            book_css.append('custom.css')

        return book_css

    def _rtl_style(self, epub_book):
        """
        Set rtl css style to the EPUB book
        """

        try:
            content = open(
                '{}/style-rtl.css'.format(self.css_dir), 'rt').read()

            item = ebooklib.epub.EpubItem(
                uid='style-rtl.css',
                content=content,
                file_name='{}/{}'.format(STYLES_DIR, 'style-rtl.css'),
                media_type='text/css'
            )

            epub_book.add_item(item)
            return 'style-rtl.css'
        except:
            return None

    def _is_cover_item(self, item):
        """
        Determines if an given item is cover type
        """

        file_name = os.path.basename(item.file_name)

        cover_types = [
            ebooklib.epub.EpubCover,
            ebooklib.epub.EpubCoverHtml
        ]

        return (
            type(item) in cover_types or file_name == 'cover.xhtml')
