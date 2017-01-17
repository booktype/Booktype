# -*- coding: utf-8 -*-
import ebooklib

from lxml import etree
from lxml.etree import strip_tags, strip_elements
from ebooklib.plugins.base import BasePlugin

from ..constants import EPUB_NOT_ALLOWED_TAGS


class CleanupTagsWriterPlugin(BasePlugin):
    """Cleanup plugin for Booktype EPUB Writing"""

    def _cleanup(self, root):
        for tag, action, replacement in [
            (i['tag'], i['action'], i['replacement'] if 'replacement' in i else None) for i in EPUB_NOT_ALLOWED_TAGS
            ]:
            if action == 'strip':
                for element in root.iter('p'):
                    strip_tags(element, tag)
            elif action == 'drop':
                for element in root.iter('p'):
                    strip_elements(element, tag, with_tail=False)
            elif action == 'replace':
                for element in root.iter(tag):
                    element.tag = replacement['tag']
                    element.attrib.clear()

                    for attrib, content in replacement['attrs']:
                        element.set(attrib, content)
            else:
                raise Exception('EPUB_NOT_ALLOWED_TAGS contains not allowed actions.')


    def html_before_write(self, book, item):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            return True

        if isinstance(item, ebooklib.epub.EpubNav):
            return True

        root = ebooklib.utils.parse_html_string(item.content)
        self._cleanup(root)
        item.content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True
