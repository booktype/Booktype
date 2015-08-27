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

from ..base import BaseConverter

logger = logging.getLogger("booktype.convert.xhtml")

TEXT_DIR = "Text"
STYLE_DIR = "Styles"
IMAGES_DIR = "Images"


class XHTMLConverter(BaseConverter):
    name = 'xhtml'

    def convert(self, original_book, output_path):
        logger.debug('[XHTML] XHTMLConverter.convert')

        self.output_file = zipfile.ZipFile(output_path, 'w')

        self._copy_items(original_book)
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

            if item_type == ebooklib.ITEM_IMAGE:
                self.output_file.writestr('{}/{}'.format(IMAGES_DIR, file_name), item.get_content())
            elif item_type == ebooklib.ITEM_DOCUMENT:
                if isinstance(item, ebooklib.epub.EpubNav):
                    # Modify nav.xhtml file from EPUB for out XHTML output
                    content = self._fix_chapter(self._clear_nav(item.get_content()))
                    self.output_file.writestr('index.xhtml', content)
                elif not isinstance(item, ebooklib.epub.EpubNcx):
                    # Ignore NCX file, everything else should be copied
                    content = self._fix_chapter(item.get_content())

                    self.output_file.writestr('{}/{}'.format(TEXT_DIR, file_name), content)

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
        Fix content of the chapter by adding styling and fix image links.
        """

        root = ebooklib.utils.parse_html_string(content)
        self._fix_images(root)

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

    def _add_styles(self):
        """
        Add Styling.
        """

        content = self.config.get('settings', {}).get('styling', u'')

        self.output_file.writestr('{}/custom.css'.format(STYLE_DIR), content)
