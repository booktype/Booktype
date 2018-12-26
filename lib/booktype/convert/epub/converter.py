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
import json
import logging
import urlparse
import ebooklib
import datetime
from copy import deepcopy
from lxml import etree

from django.template.base import Template
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from booktype.apps.themes.utils import (
    read_theme_style, read_theme_assets, read_theme_asset_content)
from booktype.apps.convert.templatetags.convert_tags import (
    get_refines, get_metadata)
from booktype.apps.convert import plugin
from booktype.convert.image_editor_conversion import ImageEditorConversion

from .writer import Epub3Writer, Epub2Writer
from .writerplugins import WriterPlugin, ImageEditorWriterPlugin, CleanupTagsWriterPlugin

from .cover import add_cover, COVER_FILE_NAME
from .constants import (
    IMAGES_DIR, STYLES_DIR, FONTS_DIR,
    DOCUMENTS_DIR, DEFAULT_LANG, EPUB_DOCUMENT_WIDTH
)

from ..base import BaseConverter
from ..utils.epub import parse_toc_nav

logger = logging.getLogger("booktype.convert.epub")


class Epub3Converter(BaseConverter):
    name = 'epub3'
    verbose_name = _('EPUB3')
    support_section_settings = True
    images_color_model = "RGB"

    toc_title = 'toc'
    default_style = 'style1'
    default_lang = DEFAULT_LANG
    writer_plugin_class = WriterPlugin
    css_dir = os.path.join(os.path.dirname(__file__), 'styles/')

    _theme_suffix = 'epub'
    _images_dir = 'images/'

    # valid extensions to assign right mimetype
    WOFF_FONTS = ['.woff']
    OPENTYPE_FONTS = ['.otf', '.otc', '.ttf', '.ttc']

    def __init__(self, *args, **kwargs):
        super(Epub3Converter, self).__init__(*args, **kwargs)

        self.images_path = os.path.join(self.sandbox_path, self._images_dir)

        self.theme_name = ''
        self.theme_plugin = None
        self._bk_image_editor_conversion = None

    def _get_theme_plugin(self):
        return plugin.load_theme_plugin(self._theme_suffix, self.theme_name)

    def _init_theme_plugin(self):
        if 'theme' in self.config:
            self.theme_name = self.config['theme'].get('id', '')
            tp = self._get_theme_plugin()
            if tp:
                self.theme_plugin = tp(self)
        else:
            self.theme_name = None

    def pre_convert(self, original_book, book):
        super(Epub3Converter, self).pre_convert(original_book)

        if self.theme_plugin:
            try:
                self.theme_plugin.pre_convert(original_book, book)
            except NotImplementedError:
                pass

        # TODO move it to more proper place in the future, and create plugin for it
        self._bk_image_editor_conversion = ImageEditorConversion(
            original_book, EPUB_DOCUMENT_WIDTH, self
        )

    def post_convert(self, original_book, book, output_path):

        if self.theme_plugin:
            try:
                self.theme_plugin.post_convert(original_book, book, output_path)
            except NotImplementedError:
                pass

    def convert(self, original_book, output_path):
        convert_start = datetime.datetime.now()

        logger.debug('[EPUB] {}.convert'.format(self.__class__.__name__))

        self._init_theme_plugin()

        epub_book = ebooklib.epub.EpubBook()
        epub_book.FOLDER_NAME = 'OEBPS'

        self.pre_convert(original_book, epub_book)

        epub_book.uid = original_book.uid
        epub_book.title = original_book.title

        # we should define better uri for this
        epub_book.add_prefix('bkterms', 'http://booktype.org/')

        epub_book.metadata = deepcopy(original_book.metadata)
        epub_book.toc = []

        self.direction = self._get_dir(epub_book)

        logger.debug('[EPUB] Edit metadata')
        self._edit_metadata(epub_book)

        logger.debug('[EPUB] Copy items')
        self._copy_items(epub_book, original_book)

        logger.debug('[EPUB] Make navigation')
        self._make_nav(epub_book, original_book)

        logger.debug('[EPUB] Add cover')
        self._add_cover(epub_book)

        if self.theme_name:
            self._add_theme_assets(epub_book)

        self.post_convert(original_book, epub_book, output_path)

        logger.debug('[EPUB] Setting writer plugins and options')
        writer_options = {'plugins': self._get_plugins(epub_book, original_book)}

        logger.debug('[EPUB] Writer')
        writer_class = self._get_writer_class()
        epub_writer = writer_class(output_path, epub_book, options=writer_options)

        logger.debug('[EPUB] Process')
        epub_writer.process()

        logger.debug('[EPUB] Write')
        epub_writer.write()

        logger.debug('[END] {}.convert'.format(self.__class__.__name__))

        convert_end = datetime.datetime.now()
        logger.info('Conversion lasted %s.', convert_end - convert_start)

        return {"size": os.path.getsize(output_path)}

    def _get_dir(self, epub_book):
        m = epub_book.metadata[ebooklib.epub.NAMESPACES["OPF"]]

        def _check(x):
            return x[1] and x[1].get('property', '') == 'bkterms:dir'

        values = filter(_check, m[None])
        if len(values) > 0 and len(values[0]) > 0:
            return values[0][0].lower()

        return 'ltr'

    def _get_writer_plugin_class(self):
        """Returns the writer plugin class to used by writer"""

        if self.writer_plugin_class:
            return self.writer_plugin_class
        raise ImproperlyConfigured

    def _get_writer_plugin(self, epub_book, original_book):
        """Returns the writer plugin instance with some default options already set up"""

        writer_plugin = self._get_writer_plugin_class()()
        opts = {
            'css': self._add_css_styles(epub_book),
            'style': self.config.get('style', self.default_style),
            'lang': self._get_language(original_book),
            'preview': self.config.get('preview', True),
            'direction': self._get_dir(epub_book)
        }

        writer_plugin.options.update(opts)
        return writer_plugin

    def _get_plugins(self, epub_book, original_book):
        """Returns the plugins to be used by writer instance"""

        writer_plugin = self._get_writer_plugin(epub_book, original_book)
        image_editor_writer_plugin = ImageEditorWriterPlugin(converter=self)
        cleanup_tags_writerplugin = CleanupTagsWriterPlugin()

        return [writer_plugin, image_editor_writer_plugin, cleanup_tags_writerplugin]

    def _get_writer_class(self):
        """Simply returns the default writer class to be used by the converter"""

        return Epub3Writer

    def _get_language(self, original_book):
        """
        Returns the book language, if there is no language in metadata (from settings)
        then we use the default language set to the class
        """

        metadata = self._get_data(original_book)
        default = metadata.get('language', self.default_lang)
        return self.config.get('lang', default)

    def _edit_metadata(self, epub_book):
        """Modifies original metadata."""

        # delete existing 'modified' tag
        m = epub_book.metadata[ebooklib.epub.NAMESPACES["OPF"]]
        m[None] = filter(lambda (_, x): not (isinstance(x, dict) and x.get("property") == "dcterms:modified"), m[None])  # noqa

        # we also need to remove the `additional metadata` which here is just garbage
        m[None] = filter(lambda (_, x): not (isinstance(x, dict) and x.get("property").startswith("add_meta_terms:")), m[None])  # noqa

        # NOTE: probably going to extend this function in future

    def _make_nav(self, epub_book, original_book):
        """Creates navigational stuff (guide, ncx, nav) by copying the original."""

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
            if type(item[1]) in (str, unicode):
                if os.path.basename(item[1]) == COVER_FILE_NAME:
                    return False
            return True

        toc = filter(_skip_cover, parse_toc_nav(original_book))
        toc = map(mapper, toc)

        # we don't allow empty sections just because epubcheck will
        # raise an error at the moment of evaluating the toc.ncx file
        toc = filter(_empty_sec, toc)

        epub_book.toc = toc

    def _copy_items(self, epub_book, original_book):
        """Populates the book by copying items from the original book"""

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
                        'href': file_name,
                        'title': self.config.get('toc_title', self.toc_title)
                    })
                    item.file_name = file_name
                else:
                    epub_book.spine.append(item)

                    if self.theme_plugin:
                        try:
                            content = ebooklib.utils.parse_html_string(item.content)
                            cnt = self.theme_plugin.fix_content(content)
                            item.content = etree.tostring(cnt, method='html', encoding='utf-8', pretty_print=True)
                        except NotImplementedError:
                            pass

                    # todo move it to more proper place in the future, and create plugin for it
                    if self._bk_image_editor_conversion:
                        try:
                            content = ebooklib.utils.parse_html_string(item.content)
                            cnt = self._bk_image_editor_conversion.convert(content)
                            item.content = etree.tostring(cnt, method='html', encoding='utf-8', pretty_print=True)
                        except:
                            logger.exception("epub ImageEditorConversion failed")

            if isinstance(item, ebooklib.epub.EpubNcx):
                item = ebooklib.epub.EpubNcx()

            epub_book.add_item(item)
            self.items_by_path[item.file_name] = item

    def _add_cover(self, epub_book):
        """Adds cover image if present in config to the resulting EPUB"""

        if 'cover_image' in self.config.keys():
            cover_asset = self.get_asset(self.config['cover_image'])
            add_cover(
                epub_book, cover_asset, self.config.get('lang', DEFAULT_LANG))

    def _get_theme_style(self):
        return read_theme_style(self.theme_name, self._theme_suffix)

    def _get_default_style(self):
        return render_to_string('themes/style_{}.css'.format(self._theme_suffix), {'dir': self.direction})

    def _add_css_styles(self, epub_book):
        """Adds default css styles and custom css text if exists in config"""

        book_css = []

        try:
            epub_book.add_item(
                ebooklib.epub.EpubItem(
                    uid='default.css',
                    content=self._get_default_style(),
                    file_name='{}/{}'.format(STYLES_DIR, 'default.css'),
                    media_type='text/css'
                )
            )
            book_css.append('default.css')
        except Exception as e:
            logger.info('Default style was not added %s.', e)

        if self.theme_name:
            content = self._get_theme_style()

            if self.theme_name == 'custom':
                try:
                    data = json.loads(self.config['theme']['custom'].encode('utf8'))

                    tmpl = Template(content)
                    content = tmpl.render(data)
                except:
                    logger.exception("Fails with custom theme.")

            item = ebooklib.epub.EpubItem(
                uid='theme.css',
                content=content,
                file_name='{}/{}'.format(STYLES_DIR, 'theme.css'),
                media_type='text/css'
            )

            epub_book.add_item(item)
            book_css.append('theme.css')

        # we need to add css from publishing settings screen
        settings_style = self.config.get('settings', {}).get('styling', None)

        if settings_style:
            item = ebooklib.epub.EpubItem(
                uid='custom_style.css',
                content=settings_style,
                file_name='{}/{}'.format(STYLES_DIR, 'custom_style.css'),
                media_type='text/css'
            )

            epub_book.add_item(item)
            book_css.append('custom_style.css')

        return book_css


    def _get_theme_assets(self):
        return read_theme_assets(self.theme_name, self._theme_suffix)

    def _add_theme_assets(self, epub_book):
        assets = self._get_theme_assets()

        for asset_type, asset_list in assets.iteritems():
            if asset_type == 'images':
                for image_name in asset_list:
                    name = os.path.basename(image_name)
                    content = read_theme_asset_content(self.theme_name, image_name)

                    if content:
                        image = ebooklib.epub.EpubImage()
                        image.file_name = "{}/{}".format(IMAGES_DIR, name)
                        image.id = 'theme_image_%s' % uuid.uuid4().hex[:5]
                        image.set_content(content)

                        epub_book.add_item(image)
            elif asset_type == 'fonts':
                for font_name in asset_list:
                    name = os.path.basename(font_name)
                    extension = os.path.splitext(font_name)[-1].lower()
                    content = read_theme_asset_content(self.theme_name, font_name)

                    if content:
                        font = ebooklib.epub.EpubItem()
                        font.file_name = "{}/{}".format(FONTS_DIR, name)
                        font.set_content(content)

                        # try to set the right font media type
                        # http://www.idpf.org/epub/301/spec/epub-publications.html#sec-core-media-types
                        if extension in self.OPENTYPE_FONTS:
                            font.media_type = 'application/vnd.ms-opentype'
                        elif extension in self.WOFF_FONTS:
                            font.media_type = 'application/font-woff'

                        epub_book.add_item(font)

    def _get_data(self, book):
        """Returns default data for the front and end matter templates.

        It mainly has default metadata from the book.

        :Returns:
          - Dictionary with default data for the templates
        """

        return {
            "title": get_refines(book.metadata, 'title-type', 'main'),
            "subtitle": get_refines(book.metadata, 'title-type', 'subtitle'),
            "shorttitle": get_refines(book.metadata, 'title-type', 'short'),
            "author": get_refines(book.metadata, 'role', 'aut'),

            "publisher": get_metadata(book.metadata, 'publisher'),
            "isbn": get_metadata(book.metadata, 'identifier'),
            "language": get_metadata(book.metadata, 'language'),

            "metadata": book.metadata
        }

    def _is_cover_item(self, item):
        """Determines if an given item is cover type"""

        file_name = os.path.basename(item.file_name)

        cover_types = [
            ebooklib.epub.EpubCover,
            ebooklib.epub.EpubCoverHtml
        ]

        return (type(item) in cover_types or file_name == 'cover.xhtml')


class Epub2Converter(Epub3Converter):
    name = 'epub2'
    verbose_name = _('EPUB2')
    support_section_settings = True
    images_color_model = "RGB"
    writer_plugin_class = WriterPlugin

    def __init__(self, *args, **kwargs):
        super(Epub2Converter, self).__init__(*args, **kwargs)

    def _get_writer_class(self):
        return Epub2Writer
