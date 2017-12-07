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
from booktype.convert.utils.epub import parse_toc_nav, get_sections_settings

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
                old_class = h.get('class', '')
                if header == 'h1' and h.getprevious() is None:
                    h.set('class', 'chapter-{} {}'.format(header, old_class))
                else:
                    h.set('class', 'body-{} {}'.format(header, old_class))

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


class TocSettings(object):
    """
    Just a dummy object with all possible valid values for section
    settings in Table of Contents
    """

    SHOW_SECTION_SHOW_CHAPTERS = 'show_section_show_chapters'
    SHOW_SECTION_HIDE_CHAPTERS = 'show_section_hide_chapters'

    HIDE_SECTION_SHOW_CHAPTERS = 'hide_section_show_chapters'
    HIDE_SECTION_HIDE_CHAPTERS = 'hide_section_hide_chapters'


class SectionsSettingsPlugin(BasePlugin):
    """
    Plugin to handle sections settings stuff which would be common for all
    the outputs
    """

    def __init__(self, *args, **kwargs):
        super(SectionsSettingsPlugin, self).__init__(*args, **kwargs)

        self.original_book = None
        self.sections_to_remove = []
        self.chapters_to_remove = []

    @staticmethod
    def build_section_key(title, count):
        """
        Generates a key to get/set the section settings

        :Args:
          - `str` title
          - `int` count to make it unique
        """
        return 'section_%s_%s' % (booktype_slugify(title), count)

    def _clean_book_items(self):
        """
        Removes the items that are not supposed to be shown according to
        section settings
        """

        output_name = self.convert.name
        settings = get_sections_settings(self.original_book)

        count = 1

        # mark chapters and sections to be removed (if any)
        for toc_item in parse_toc_nav(self.original_book):
            if isinstance(toc_item[1], list):
                section_title, chapters = toc_item

                key = self.build_section_key(section_title, count)
                section_settings = json.loads(settings.get(key, '{}'))
                show_in_outputs = section_settings.get('show_in_outputs', {})

                # means to remove the chapters that belongs to this section
                if not show_in_outputs.get(output_name, True):
                    self.chapters_to_remove += [x[1] for x in chapters]
                    self.sections_to_remove.append(key)

                # increment if a section is found
                count += 1

        # now let's loop over all the book items and exclude the ones are marked to be removed
        new_items = []
        for i, item in enumerate(list(self.original_book.items)):
            if item.get_name() not in self.chapters_to_remove:
                new_items.append(item)

        self.original_book.items = new_items

    def _mark_chapter_content(self, content, mark_as):
        if not mark_as:
            return content

        content = ebooklib.utils.parse_html_string(content)
        content = content.find('body')

        content.tag = 'div'
        content.set('class', mark_as)

        return etree.tostring(content, method='html', encoding='utf-8', pretty_print=True)

    def _fix_nav_content(self):
        """Just fixes the nav content according to the sections to be removed"""

        output_name = self.convert.name
        settings = get_sections_settings(self.original_book)
        nav_item = next((item for item in self.original_book.items if isinstance(item, ebooklib.epub.EpubNav)), None)

        if nav_item:
            html_node = ebooklib.utils.parse_html_string(nav_item.content)
            nav_node = html_node.xpath('//nav[@*="toc"]')[0]
            list_node = nav_node.find('ol')

            # loop over sections element, they should be in the same order as
            # they were in parse_toc_nav(original_book)
            count = 1
            for item_node in list_node.findall('li'):
                sublist_node = item_node.find('ol')

                if sublist_node is not None:
                    section_name = item_node[0].text

                    section_key = self.build_section_key(section_name, count)
                    section_settings = json.loads(settings.get(section_key, '{}'))
                    toc_setting = section_settings.get('toc', {}).get(output_name, '')
                    mark_section_as = section_settings.get('mark_section_as', None)

                    # check if custom mark was given
                    if mark_section_as == 'custom':
                        mark_section_as = section_settings.get('custom_mark', None)

                    if mark_section_as and section_key not in self.sections_to_remove:
                        for item in sublist_node.iterchildren('li'):
                            chapter_href = item[0].get('href')
                            item = self.original_book.get_item_with_href(chapter_href)
                            item.content = self._mark_chapter_content(item.content, mark_section_as)

                    # if whole section is hidden, we should also remove
                    # the whole entry in the TOC in the EpubNav file
                    # cause why to show the toc entry if section content is hidden? :)
                    if section_key in self.sections_to_remove:
                        item_node.drop_tree()
                    else:
                        if toc_setting == TocSettings.SHOW_SECTION_SHOW_CHAPTERS:
                            pass  # nothing to do here :)

                        elif toc_setting == TocSettings.HIDE_SECTION_SHOW_CHAPTERS:
                            # removing section label/title
                            section_label = item_node[0]
                            item_node.remove(section_label)

                            parent = item_node.getparent()
                            index = parent.index(item_node)

                            for child in sublist_node.iterchildren('li'):
                                parent.insert(index, child)
                                index += 1

                            # now removing the empty sublist_node
                            sublist_node.getparent().remove(sublist_node)

                        elif toc_setting == TocSettings.SHOW_SECTION_HIDE_CHAPTERS:
                            # section name should point to first chapter under it
                            # otherwise it doesn't make sense to show just the label
                            # AND because we have a filter to remove empty sections :)
                            parent = item_node.getparent()
                            index = parent.index(item_node)

                            if len(sublist_node) > 0:
                                section_label = item_node[0]
                                item_node.remove(section_label)

                                child = sublist_node[0]
                                child[0].text = section_label.text
                                parent.insert(index, child)

                                sublist_node.getparent().remove(sublist_node)

                        elif toc_setting == TocSettings.HIDE_SECTION_HIDE_CHAPTERS:
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
