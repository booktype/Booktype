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
import json
from lxml import etree

import urllib2
import logging

import ebooklib
import ebooklib.epub
import ebooklib.utils

from copy import deepcopy

from ..base import BaseConverter
from ..utils.epub import parse_toc_nav
from .. import utils
from .styles import create_default_style, get_page_size

from django.conf import settings
from django.template.loader import render_to_string


logger = logging.getLogger("booktype.convert.pdf")


class MPDFConverter(BaseConverter):
    name = "mpdf"

    _images_dir = "images/"
    _body_pdf_name = "body.pdf"
    _body_html_name = "body.html"

    _html_template = "<body></body>"

    def __init__(self, *args, **kwargs):
        super(MPDFConverter, self).__init__(*args, **kwargs)

        # absolute path to directory where images are saved
        self.images_path = os.path.join(self.sandbox_path, self._images_dir)
        # image item name -> file name mappings
        self.images = {}
        self.n = 0

    def convert(self, book, output_path):
        self._save_images(book)

        # Not that much needed at the moment
        self.config['page_width'], self.config['page_height'] = get_page_size(self.config['settings'])

        dc_metadata = {
            key: value[0][0] for key, value in
            book.metadata.get("http://purl.org/dc/elements/1.1/").iteritems()
        }

        head_params = {
            "title": dc_metadata.get("title", ""),
            "license": dc_metadata.get("rights", ""),
            "copyright": dc_metadata.get("creator", ""),
        }

        document = ebooklib.utils.parse_html_string(
            self._html_template % head_params)

        self._document_body = document.find("body")
        self._items_by_path = {
            item.file_name: item for item in
            book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        }
        map(self._write_toc_item, parse_toc_nav(book))

        html_path = os.path.join(self.sandbox_path, self._body_html_name)
        pdf_path = os.path.join(self.sandbox_path, self._body_pdf_name)

        with open(html_path, "w") as file:
            html_text = etree.tostring(
                document, method='html', pretty_print=True)
            file.write(html_text.encode("utf-8"))

        self._write_configuration(dc_metadata)
        self._create_frontmatter(dc_metadata)
        self._write_style()

        self._run_renderer(html_path, pdf_path)

        os.rename(pdf_path, output_path)

        return {"pages": 21, "size": os.path.getsize(output_path)}

    def _write_style(self):
        if 'settings' not in self.config:
            return

        css_style = create_default_style(self.config)

        f = open('{}/style.css'.format(self.sandbox_path), 'wt')
        f.write(css_style.encode('utf8'))
        f.close()

    def _write_configuration(self, dc_metadata):
        f = open('{}/config.json'.format(self.sandbox_path), 'wt')
        data = {'metadata': dc_metadata, 'config': self.config}
        f.write(unicode(json.dumps(data), 'utf8').encode('utf8'))
        f.close()

    def _write_toc_item(self, toc_item):
        if isinstance(toc_item[1], list):
            section_title, chapters = toc_item
            map(self._write_toc_item, chapters)
        else:
            chapter_title, chapter_href = toc_item
            self._write_chapter_content(chapter_title, chapter_href)

    def _write_chapter_content(self, chapter_title, chapter_href):
        chapter_item = self._items_by_path[chapter_href]
        base_path = os.path.dirname(chapter_item.file_name)

        chapter = ebooklib.utils.parse_html_string(chapter_item.content)

        if self.n > 0:
            pb = etree.Element("pagebreak")  # , {'pagenumstyle': '1'})
            self._document_body.append(pb)

        #tc = etree.Element("tocentry")
        #self._document_body.append(tc)

        for chapter_child in chapter.find("body"):
            content = deepcopy(chapter_child)
            self._fix_images(content, base_path)
            self._document_body.append(content)

        self.n += 1

    def _save_images(self, book):
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)

        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            self._save_image(item)

    def _save_image(self, item):
        file_name = os.path.basename(item.file_name)
        file_path = os.path.join(self.images_path, file_name)

        if os.path.exists(file_path):
            file_name = '{}-{}'.format(item.id, file_name)
            file_path = os.path.join(self.images_path, file_name)

        with open(file_path, 'wb') as file:
            file.write(item.content)

        self.images[item.file_name] = file_name

    def _fix_images(self, root, base_path):
        for element in root.iter('img'):
            src_url = urllib2.unquote(element.get('src'))
            item_name = os.path.normpath(os.path.join(base_path, src_url))
            try:
                file_name = self.images[item_name]
                element.set('src', self._images_dir + file_name)
            except Exception as e:
                # TODO: discuss what to do in case of missing image
                logger.error(
                    'MPDF::_fix_images: image not found %s (%s)' %
                    (item_name, e)
                )
                continue

    def _create_frontmatter(self, dc_metadata):
        data = {"title": dc_metadata.get("title", ""),
            "license": dc_metadata.get("rights", ""),
            "copyright": dc_metadata.get("creator", ""),
        }

        html = render_to_string('convert/frontmatter_mpdf.html', data)

        f = open('{}/frontmatter.html'.format(self.sandbox_path), 'wt')
        f.write(html.encode('utf-8'))
        f.close()

    def _run_renderer(self, html_path, pdf_path):
        MPDF_DIR = settings.MPDF_DIR
        PHP_PATH = settings.PHP_PATH
        MPDF_SCRIPT = settings.MPDF_SCRIPT

        params = ['--mpdf={}'.format(MPDF_DIR),
                  '--dir={}'.format(self.sandbox_path),
                  '--output={}'.format(pdf_path)]

        cmd = [PHP_PATH, MPDF_SCRIPT] + params

        try:
            utils.run_command(cmd)
        except Exception as e:
            logger.error(
                'MPDF Converter::Fail running the command "{}".'.format(e))
