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

from lxml import etree

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string

from booktype.utils.tidy import tidy_cleanup


class TidyPlugin(BasePlugin):
    NAME = 'Tidy HTML'
    OPTIONS = {
        # 'utf8': None,
        # 'anchor-as-name': 'no',
        'tidy-mark': 'no',
        'drop-font-tags': 'yes',
        'uppercase-attributes': 'no',
        'uppercase-tags': 'no'
    }

    def __init__(self, extra={}):
        self.options = dict(self.OPTIONS)
        self.options.update(extra)

    def html_after_read(self, book, chapter):
        if not chapter.content:
            return None

        (_, chapter.content) = tidy_cleanup(chapter.get_content(), **self.options)

        return chapter.content


class ImportPlugin(BasePlugin):
    NAME = 'Import Plugin'

    def __init__(self, remove_attributes=None):
        if remove_attributes:
            self.remove_attributes = remove_attributes
        else:
            # different kind of onmouse
            self.remove_attributes = ['class', 'style', 'onkeydown', 'onkeypress', 'onkeyup',
                                      'onclick', 'ondblclik', 'ondrag', 'ondragend', 'ondragenter',
                                      'ondragleave', 'ondragover', 'ondragstart', 'ondrop',
                                      'onmousedown', 'onmousemove', 'onmouseout', 'onmouseover',
                                      'onmouseup', 'onmousewheel', 'onscroll']

    def html_after_read(self, book, chapter):
        try:
            tree = parse_html_string(chapter.content)
        except:
            return

        root = tree.getroottree()

        if len(root.find('head')) != 0:
            head = tree.find('head')
            title = head.find('title')

            if title is not None:
                chapter.title = title.text

        if len(root.find('body')) != 0:
            body = tree.find('body')

            # todo:
            # - fix <a href="">
            # - fix ....

            for _item in body.iter():
                for t in self.remove_attributes:
                    if t in _item.attrib:
                        del _item.attrib[t]

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
