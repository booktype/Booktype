# This file is part of Booktype.
# Copyright (c) 2015 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import json
import logging
import importlib
import ebooklib
from lxml import etree

from booktype.utils import config
from booktype.utils.misc import booktype_slugify
from booktype.convert.utils.epub import parse_toc_nav

from .templatetags.convert_tags import _get_property

logger = logging.getLogger("booktype.convert")


class BasePlugin(object):
    def __init__(self, convert):
        """Base abstract class for all Theme plugins.

        :Args:
          - convert: Conversion object
        """

        self.convert = convert


class ExternalScriptPlugin(BasePlugin):
    """
    Base class for all Theme plugins which will execute external
    script to produce output file.
    """

    def pre_convert(self, book):
        """Called before conversion process starts.

        :Args:
          - book: EPUB object for input file
        """
        raise NotImplementedError

    def post_convert(self, book, output_path):
        """Called when conversion process has ended.

        :Args:
          - book: EPUB object for input file
          - output_path: File path for output file
        """
        raise NotImplementedError

    def fix_content(self, content):
        """Transform chapter content.

        This method is used to modify content of each content. This is used when
        we need to add certain elements or classes to prepare the content mPDF
        rendering.

        :Args:
          - content: lxml element object
        """
        raise NotImplementedError


class MPDFPlugin(ExternalScriptPlugin):
    """Base class for mPDF themes"""

    def get_mpdf_config(self):
        """Returns mPDF options required for this theme.

        There are always certain mPDF options which are required for different
        themes. Instead of setting global mPDF configuration it is also
        possible to define it per theme.

        :Returns:
          - Returns dictionary with mPDF options for this theme.
        """
        return {
            'mirrorMargins': True,
            'useSubstitutions': False
        }

    def fix_content(self, content):
        headers = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        for header in headers:
            for idx, h in enumerate(content.xpath('.//{}'.format(header))):
                if header == 'h1' and h.getprevious() is None:
                    h.set('class', 'chapter-{}'.format(header))
                else:
                    h.set('class', 'body-{}'.format(header))

        for quote in content.xpath(".//p[@class='quote']"):
            div = etree.Element('div', {'class': 'quote'})
            div1 = etree.Element('div', {'class': 'quote-before'})
            div1.text = '"'

            quote.tag = 'div'
            quote.set('class', 'quote-content')

            quote.addprevious(div)
            div.insert(0, div1)
            div.insert(1, quote)

        # let's fix the cite tags
        for cite in content.xpath(".//p[@class='bk-cite']"):
            cite.tag = 'cite'

        # set body-first class to first child inside box-content divs [infobox]
        for box_content in content.xpath(".//div[@class='box-content']"):
            for idx, p in enumerate(box_content.xpath('.//p')):
                if p.get('class', '') != '':
                    continue

                if idx == 0:
                    p.set('class', 'body-first')

        for idx, p in enumerate(content.xpath(".//p")):
            if p.get('class', '') != '':
                continue

            prev = p.getprevious()
            if prev is not None and prev.tag in headers:
                p.set('class', 'body-first')
            else:
                p.set('class', 'body')

        return content


class ConversionPlugin(BasePlugin):
    """Base class for theme plugins which are not using external scripts
    to create required content.
    """

    def pre_convert(self, original_book, book):
        """Called before conversion process starts.

        :Args:
          - original_book:
          - book:
        """
        raise NotImplementedError

    def post_convert(self, original_book, book, output_path):
        """Called when conversion process has ended.

        :Args:
          - original_book:
          - output_path:
          -
        """
        raise NotImplementedError

    def fix_content(self, content):
        """Transform chapter content.

        :Args:
          - content: lxml element object
        """

        raise NotImplementedError


class SectionsSettingsPlugin(BasePlugin):
    """
    Plugin to handle sections settings stuff which would be common for all
    the outputs
    """

    def __init__(self, *args, **kwargs):
        super(SectionsSettingsPlugin, self).__init__(*args, **kwargs)

        self.sections_to_remove = []
        self.chapters_to_remove = []

    def _get_section_key(self, title, count):
        return 'section_%s_%s' % (booktype_slugify(title), count)

    def _clean_book_items(self):
        """
        Removes the items that are not supposed to be shown according to
        section settings
        """

        output_name = self.convert.name
        settings = _get_property(self.original_book.metadata, 'bkterms:sections_settings')
        try:
            settings = json.loads(settings)
        except:
            settings = {}

        count = 1

        for toc_item in parse_toc_nav(self.original_book):
            if isinstance(toc_item[1], list):
                section_title, chapters = toc_item

                key = self._get_section_key(section_title, count)
                section_settings = json.loads(settings.get(key, '{}'))
                hide_in_outputs = section_settings.get('hide_in_outputs', {})

                # means to remove the chapters that belongs to this section
                if hide_in_outputs.get(output_name, False):
                    self.chapters_to_remove += [x[1] for x in chapters]
                    self.sections_to_remove.append(key)

                # increment if a section if found
                count += 1

        new_items = []
        for i, item in enumerate(list(self.original_book.items)):
            if item.get_name() not in self.chapters_to_remove:
                new_items.append(item)

        self.original_book.items = new_items

    def _fix_nav_content(self):
        """Just fixes the nav content according to the sections to be removed"""

        nav_item = next((item for item in self.original_book.items if isinstance(item, ebooklib.epub.EpubNav)), None)
        if nav_item:
            html_node = ebooklib.utils.parse_html_string(nav_item.content)
            nav_node = html_node.xpath('//nav[@*="toc"]')[0]
            list_node = nav_node.find('ol')

            # loop over sections element, they might be in the same order as
            # they were in parse_toc_nav(original_book)
            count = 1
            for item_node in list_node.findall('li'):
                sublist_node = item_node.find('ol')

                if sublist_node is not None:
                    section_name = item_node[0].text
                    key = self._get_section_key(section_name, count)

                    if key in self.sections_to_remove:
                        item_node.drop_tree()

                    # increment if a section is found
                    count += 1

            nav_item.content = etree.tostring(
                html_node, pretty_print=True, encoding='utf-8', xml_declaration=True)

    def pre_convert(self, original_book):
        """
        Checks if the content should go into the current output
        according to the settings. Should also do some other checks

        :Args:
          - original_book:
        """
        self.original_book = original_book
        self._clean_book_items()
        self._fix_nav_content()


def load_theme_plugin(convert_type, theme_name):
    """Load theme plugin for certain conversion and theme. Returns reference
    to plugin theme which has to be initialised later on.

    :Args:
      - convert_type: Type of conversion (mpdf, screenpdf, epub, ...)
      - theme_name: Theme name

    :Returns:
      Returns reference to plugin class which has to be initialised.
    """

    plgn = None

    plugins = config.get_configuration('BOOKTYPE_THEME_PLUGINS')

    try:
        module_name = plugins.get(theme_name, None)

        if module_name:
            module = importlib.import_module(module_name)
            plgn = module.__convert__.get(convert_type, None)
            return plgn
    except:
        logger.exception('Can not load the theme plugin.')

    return plgn
