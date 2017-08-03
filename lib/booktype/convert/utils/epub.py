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
import ebooklib
import ebooklib.epub
import ebooklib.utils
from lxml import etree

from booktype.apps.convert.templatetags.convert_tags import _get_property


def parse_toc_nav(book):
    nav_item = next((item for item in book.items if isinstance(item, ebooklib.epub.EpubNav)), None)

    if nav_item is None:
        raise Exception("could not find the 'nav' item")

    # directory containing the nav document
    base_name = os.path.dirname(nav_item.file_name)

    return _parse_nav_content(nav_item.content, base_name)


def _parse_nav_content(content, base_name):
    html_node = ebooklib.utils.parse_html_string(content)
    nav_node = html_node.xpath("//nav[@*='toc']")[0]

    def parse_list(list_node):
        items = []

        for item_node in list_node.findall("li"):

            sublist_node = item_node.find("ol")
            link_node = item_node.find("a")

            if sublist_node is not None:
                section_name = item_node[0].text
                chapters = parse_list(sublist_node)
                items.append((section_name, chapters))

            elif link_node is not None:
                chapter_name = link_node.text
                chapter_path = os.path.normpath(os.path.join(base_name, link_node.get("href")))

                items.append((chapter_name, chapter_path))

        return items

    return parse_list(nav_node.find("ol"))


def parse_toc_ncx(book):
    raise NotImplementedError("NCX parsing not implemented")


def reformat_endnotes(chapter_content):
    """Insert internal link to endnote's body into the sup tag.
       Can be used in epub2/xhtml/screenPdf formats

    :Args:
      - chapter_content: lxml node tree with the chapter content

    """

    for sup in chapter_content.iter('sup'):
        if sup.get('data-id'):
            a = etree.Element("a")
            a.set('href', '#endnote-{0}'.format(sup.get('data-id')))
            a.text = sup.text
            sup.text = ''
            sup.insert(0, a)
            del sup.attrib['data-id']


def get_sections_settings(epub_book):
    """
    Reads a from the bookmetadata and returns it as dict object
    """

    # TODO: put bkterms:sections_settings meta key into safest place, like constants module
    settings = _get_property(epub_book.metadata, 'bkterms:sections_settings')
    try:
        settings = json.loads(settings)
    except:
        settings = {}

    return settings
