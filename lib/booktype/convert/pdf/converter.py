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

from copy import deepcopy

import lxml
import lxml.html
from lxml import etree

import urllib2

import logging

import ebooklib
import ebooklib.epub
import ebooklib.utils

from ..base import BaseConverter
from . import bookjs


logger = logging.getLogger("booktype.convert")


class PdfConverter(BaseConverter):
    name = "pdf"

    _images_dir = "images/"
    _body_pdf_name = "body.pdf"
    _body_html_name = "body.html"

    _html_template = """
<html>
<head>
  <title>%(title)s</title>
  <meta name="license" content="%(license)s" />
  <meta name="copyright" content="%(copyright)s" />
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
</head>
<body></body>
</html>
"""

    def __init__(self, *args, **kwargs):
        super(PdfConverter, self).__init__(*args, **kwargs)
        # absolute path to directory where images are saved
        self.images_path = os.path.join(self.sandbox_path, self._images_dir)
        # image item name -> file name mappings
        self.images = {}


    def convert(self, book, output_path):
        self._save_images(book)

        dc_metadata = {key : value[0][0] for (key, value) in book.metadata.get("http://purl.org/dc/elements/1.1/").iteritems()}

        head_params = {
            "title"     : dc_metadata.get("title", ""),
            "license"   : dc_metadata.get("rights", ""),
            "copyright" : dc_metadata.get("creator", ""),
        }

        document = ebooklib.utils.parse_html_string(self._html_template % head_params)
        document_body = document.find("body")

        document_items = {item.id : item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)}

        for item_id, linear in book.spine:
            item = document_items[item_id]

            base_path = os.path.dirname(item.file_name)

            chapter = ebooklib.utils.parse_html_string(item.content)
            chapter_body = chapter.find("body")

            for chapter_child in chapter_body:
                content = deepcopy(chapter_child)
                self._fix_images(content, base_path)
                document_body.append(content)

        html_path = os.path.join(self.sandbox_path, self._body_html_name)
        pdf_path  = os.path.join(self.sandbox_path, self._body_pdf_name)

        with open(html_path, "w") as file:
            html_text = etree.tostring(document, method='html')
            file.write(html_text.encode("utf-8"))

        self._run_renderer(html_path, pdf_path)


    def _save_images(self, book):
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)

        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            self._save_image(item)

    def _save_image(self, item):
        file_name = os.path.basename(item.file_name)
        file_path = os.path.join(self.images_path, file_name)

        if os.path.exists(file_path):
            file_name = "{}-{}".format(item.id, file_name)
            file_path = os.path.join(self.images_path, file_name)

        with open(file_path, "wb") as file:
            file.write(item.content)

        self.images[item.file_name] = file_name


    def _fix_images(self, root, base_path):
        for element in root.iter("img"):
            src_url = urllib2.unquote(element.get("src"))
            item_name = os.path.normpath("{}/{}".format(base_path, src_url))
            file_name = self.images[item_name]
            element.set("src", self._images_dir + file_name)


    def _run_renderer(self, html_path, pdf_path):
        bookjs.render(html_path, pdf_path)
