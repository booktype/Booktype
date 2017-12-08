# -*- coding: utf-8 -*-
import ebooklib

from lxml import etree
from lxml.etree import strip_tags, strip_elements
from ebooklib.plugins.base import BasePlugin

from ..constants import EPUB_NOT_ALLOWED_TAGS, EPUB_AVAILABLE_INBODY_ROOT_TAGS, EPUB_ALLOWED_TAG_ATTRS


class CleanupTagsWriterPlugin(BasePlugin):
    """Cleanup plugin for Booktype EPUB Writing"""

    @staticmethod
    def _cleanup(root):
        for x in EPUB_NOT_ALLOWED_TAGS:
            tag, action, replacement = x['tag'], x['action'], x.get('replacement', None)

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

    @staticmethod
    def _cleanup_root(root):
        """
        Check if chapter's root tag is fit epubcheck requirements
        :param root: lxml.html.HtmlElement
        """

        for body in root.xpath('//body'):
            for child in body.getchildren():
                if child.tag not in EPUB_AVAILABLE_INBODY_ROOT_TAGS:
                    child.tag = 'p'
                    child.attrib.clear()

    @staticmethod
    def _cleanup_attrs(root):
        """
        Cleanup attributes which are not fit epubcheck requirements
        :param root: lxml.html.HtmlElement
        """

        # Check all elements with attr "id" exists
        # XML ID's are not allowed to start with a number!
        for element in root.xpath('//*[@id]'):
            if element.attrib['id'][0].isdigit():
                del element.attrib['id']

        # remove not allowed tags
        # required to fit epubcheck requirements
        for tag, permitted_attrs in EPUB_ALLOWED_TAG_ATTRS:
            for element in root.iter(tag):
                not_allowed_keys = set(element.attrib.keys()) - set(permitted_attrs)
                for attr_key in not_allowed_keys:
                    del element.attrib[attr_key]

    def html_before_write(self, book, item):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            return True

        if isinstance(item, ebooklib.epub.EpubNav):
            return True

        root = ebooklib.utils.parse_html_string(item.content)
        self._cleanup_root(root)
        self._cleanup_attrs(root)
        self._cleanup(root)
        item.content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True
