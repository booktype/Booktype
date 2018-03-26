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
import urllib
import zipfile

import ebooklib
from lxml import etree

from django.utils.translation import ugettext_lazy as _

from booktype.convert.image_editor_conversion import ImageEditorConversion
from booktype.utils import config

from ..base import BaseConverter
from ..utils.epub import reformat_endnotes

logger = logging.getLogger("booktype.convert.xhtml")

TEXT_DIR = "Text"
STYLE_DIR = "Styles"
IMAGES_DIR = "Images"
XHTML_DOCUMENT_WIDTH = config.get_configuration('XHTML_DOCUMENT_WIDTH')


class XHTMLConverter(BaseConverter):
    name = 'xhtml'
    verbose_name = _('XHTML')
    support_section_settings = False
    images_color_model = "RGB"

    _images_dir = "images/"

    def __init__(self, *args, **kwargs):
        super(XHTMLConverter, self).__init__(*args, **kwargs)
        self.images_path = os.path.join(self.sandbox_path, self._images_dir)
        self._bk_image_editor_conversion = None
        self._all_images_src = set()

    def pre_convert(self, book):
        """Called before entire process of conversion is called.

        :Args:
          - book: EPUB book object
        """

        super(XHTMLConverter, self).pre_convert(book)

        # create image edtor conversion instance
        # todo move it to more proper place in the future, and create plugin for it
        self._bk_image_editor_conversion = ImageEditorConversion(
            book, XHTML_DOCUMENT_WIDTH, self
        )

    def convert(self, original_book, output_path):
        logger.debug('[XHTML] XHTMLConverter.convert')

        self.output_file = zipfile.ZipFile(output_path, 'w')

        self.pre_convert(original_book)
        self._copy_items(original_book)
        self._write_images()
        self._add_styles()

        self.output_file.close()

        return {"size": os.path.getsize(output_path)}

    def _copy_items(self, original_book):
        """
        Populates the book by copying items from the original book
        """

        for item in original_book.get_items():
            item_type = item.get_type()
            file_name = os.path.basename(item.file_name)

            if item_type == ebooklib.ITEM_DOCUMENT:

                if isinstance(item, ebooklib.epub.EpubNav):
                    # Modify nav.xhtml file from EPUB for out XHTML output
                    content = self._fix_chapter(self._clear_nav(item.get_content()))
                    self.output_file.writestr('index.xhtml', content)
                elif not isinstance(item, ebooklib.epub.EpubNcx):
                    # Ignore NCX file, everything else should be copied
                    content = self._fix_chapter(item.get_content())

                    self.output_file.writestr('{}/{}'.format(TEXT_DIR, file_name), content)

    def _write_images(self):
        for src in self._all_images_src:
            file_name = os.path.basename(src)

            try:
                with open(src, 'r') as img:
                    self.output_file.writestr('{}/{}'.format(IMAGES_DIR, file_name), img.read())
            except IOError:
                logger.exception("xhtml. Failed to open image for writing.")

    def _clear_nav(self, content):
        """
        Modify navigation page by fixing links and removing unwanted tags.
        """

        root = ebooklib.utils.parse_html_string(content)
        etree.strip_tags(root, 'nav')

        for _a in root.xpath('//a'):
            _a.set('href', '{}/{}'.format(TEXT_DIR, _a.get('href', '')))

        return etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

    def _fix_chapter(self, content):
        """
        Fix content of the chapter by adding styling, fix image links and reformat endnotes.
        """

        root = ebooklib.utils.parse_html_string(content)

        # todo move it to more proper place in the future, and create plugin for it
        if self._bk_image_editor_conversion:
            try:
                root = self._bk_image_editor_conversion.convert(root)
            except:
                logger.exception("xhtml. ImageEditorConversion failed.")

        # save all images src
        for img_element in root.iter('img'):
            if img_element.get('src'):
                self._all_images_src.add(img_element.get('src'))

        self._fix_images(root)
        self._reformat_endnotes(root)

        head = root.find('head')

        if head is not None:
            _lnk = etree.SubElement(head, "link", {"href": "../{}/custom.css".format(STYLE_DIR), "rel": "stylesheet", "type": "text/css"})

        return etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

    def _fix_images(self, root):
        """
        Fix the path of the images to match with IMAGES_DIR
        """

        for element in root.iter('img'):

            path = urllib.unquote(element.get('src'))

            # if hostname, then it is an image with absolute url
            if urlparse.urlparse(path).hostname:
                continue

            try:
                path = path.decode('utf-8')
            except:
                pass

            file_name = os.path.basename(path)
            element.set('src', "../{}/{}".format(IMAGES_DIR, file_name))

    def _reformat_endnotes(self, root):
        """Insert internal link to endnote's body into the sup tag.

        :Args:
          - root: lxml node tree with the chapter content
        """
        reformat_endnotes(root)

    def _add_styles(self):
        """
        Add Styling.
        """

        content = self.config.get('settings', {}).get('styling', u'')

        self.output_file.writestr('{}/custom.css'.format(STYLE_DIR), content)
