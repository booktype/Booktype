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
import codecs
import urllib2
import logging
from lxml import etree


import ebooklib
import ebooklib.epub
import ebooklib.utils

from copy import deepcopy

from ..base import BaseConverter
from ..utils.epub import parse_toc_nav
from .. import utils
from .styles import create_default_style, get_page_size, CROP_MARGIN
from booktype.apps.themes.utils import read_theme_style, get_single_frontmatter, get_single_endmatter

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

    def pre_convert(self, book):
        # Not that much needed at the moment
        self.config['page_width'], self.config['page_height'] = get_page_size(self.config['settings'])

        try:
            if 'crop_marks' in self.config['settings'] and self.config['settings']['crop_marks'] == 'on':
                crop_margin = CROP_MARGIN
            else:
                crop_margin = 0

            self.config['page_width_bleed'] = int(round(self.config['page_width'] + crop_margin))
            self.config['page_height_bleed'] = int(round(self.config['page_height'] + crop_margin))
        except:
            self.config['page_width_bleed'] = self.config['page_width']
            self.config['page_height_bleed'] = self.config['page_height']

    def get_metadata(self, book):
        dc_metadata = {
            key: value[0][0] for key, value in
            book.metadata.get("http://purl.org/dc/elements/1.1/").iteritems()
        }

        return dc_metadata

    def convert(self, book, output_path):
        if 'theme' in self.config:
            self.theme_name = self.config['theme'].get('id', '')

        self.pre_convert(book)

        self._save_images(book)

        dc_metadata = self.get_metadata(book)

        document = ebooklib.utils.parse_html_string(self._html_template)

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

        self._write_configuration(book, dc_metadata)
        self._create_frontmatter(book, dc_metadata)
        self._create_endmatter(book, dc_metadata)

        self._write_style(book)

        data_out = self._run_renderer(html_path, pdf_path)

        os.rename(pdf_path, output_path)

        return {"pages": data_out.get('pages', 0), "size": os.path.getsize(output_path)}

    def get_extra_style(self, book):
        return {}

    def _write_style(self, book):
        if 'settings' not in self.config:
            return

        css_style = create_default_style(self.config, self.name, self.get_extra_style(book))
        theme_style = u''

        if self.theme_name != '':
            theme_style = read_theme_style(self.theme_name, self.name)

        custom_style = self.config.get('settings', {}).get('styling', u'')

        f = codecs.open('{}/style.css'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(css_style)
        f.write(theme_style)
        f.write(custom_style)        
        f.close()

    def get_extra_configuration(self):
        return {'mirror_margins': True}

    def _write_configuration(self, book, dc_metadata):
        data = {'metadata': dc_metadata, 'config': self.config}
        data.update(self.get_extra_configuration())

        f = codecs.open('{}/config.json'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(unicode(json.dumps(data), 'utf8'))
        f.close()

    def _write_toc_item(self, toc_item):
        if isinstance(toc_item[1], list):
            section_title, chapters = toc_item
            map(self._write_toc_item, chapters)
        else:
            chapter_title, chapter_href = toc_item
            self._write_chapter_content(chapter_title, chapter_href)

    def chapter_separator(self, chapter_title, chapter_href):
        if self.n > 0:
            pb = etree.Element("pagebreak")  # , {'pagenumstyle': '1'})
            self._document_body.append(pb)

        tc = etree.Element("tocentry", {"content": chapter_title})
        self._document_body.append(tc)

    def _write_chapter_content(self, chapter_title, chapter_href):
        chapter_item = self._items_by_path[chapter_href]
        base_path = os.path.dirname(chapter_item.file_name)

        chapter = ebooklib.utils.parse_html_string(chapter_item.content)

        self.chapter_separator(chapter_title, chapter_href)

        for chapter_child in chapter.find("body"):
            content = deepcopy(chapter_child)
            self._fix_images(content, base_path)
            content = self._fix_content(content)

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

    def _fix_content(self, content):
        if content is None:
            return content

        # For print edition we need URL outside of a tags
        for link in content.iter('a'):
            if link.attrib.get('href', '') != '':
                text = link.tail or ''
                link.tail = ' [' + link.attrib.get('href', '') + '] ' + text
                link.tag = 'span'

        # Fix links to other URL places
        return content

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

    def get_extra_data(self, book):
        return {}

    def _create_frontmatter(self, book, dc_metadata):
        data = {
            "title": dc_metadata.get("title", ""),
            "license": dc_metadata.get("rights", ""),
            "copyright": dc_metadata.get("creator", ""),
            "isbn": dc_metadata.get("identifier", ""),
        }
        data.update(self.get_extra_data(book))

        if self.theme_name != '':
            frontmatter_name = get_single_frontmatter(self.theme_name, self.name)
        else:
            frontmatter_name = 'frontmatter_{}.html'.format(self.name)

        html = render_to_string('convert/{}'.format(frontmatter_name), data)

        f = codecs.open('{}/frontmatter.html'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(html)
        f.close()

    def _create_endmatter(self, book, dc_metadata):
        data = {
            "title": dc_metadata.get("title", ""),
            "license": dc_metadata.get("rights", ""),
            "copyright": dc_metadata.get("creator", ""),
        }
        data.update(self.get_extra_data(book))

        if self.theme_name != '':
            endmatter_name = get_single_endmatter(self.theme_name, self.name)
        else:
            endmatter_name = 'endmatter_{}.html'.format(self.name)

        html = render_to_string('convert/{}'.format(endmatter_name), data)

        f = codecs.open('{}/endmatter.html'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(html)
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
            (_, out, err) = utils.run_command(cmd)
            data = json.loads(out)

            return data
        except Exception as e:
            logger.error(
                'MPDF Converter::Fail running the command "{}".'.format(e))

        return {}
