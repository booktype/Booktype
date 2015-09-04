# -*- coding: utf-8 -*-
import os
import urllib
import urlparse
import ebooklib

from lxml import etree
from ebooklib.plugins.base import BasePlugin

from ..utils.epub import reformat_endnotes
from .constants import (
    STYLES_DIR, IMAGES_DIR,
    DEFAULT_LANG, EPUB_VALID_IMG_ATTRS
)


class WriterPlugin(BasePlugin):
    """
    Basic plugin for Booktype EPUB Writing
    """

    def __init__(self, *args, **kwargs):
        super(WriterPlugin, self).__init__(*args, **kwargs)
        self.options = {}

    def html_before_write(self, book, item):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            return True

        for css_file in self.options.get('css', []):
            item.add_link(
                href='../{}/{}'.format(STYLES_DIR, css_file),
                rel='stylesheet', type='text/css')

        if isinstance(item, ebooklib.epub.EpubNav):
            return True

        item.lang = self.options.get('lang', DEFAULT_LANG)

        root = ebooklib.utils.parse_html_string(item.content)
        self._fix_images(root)
        self._reformat_endnotes(root)

        item.content = etree.tostring(
            root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True

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

            # remove not allowed attributes from image element
            for attr in frozenset(element.keys()) - EPUB_VALID_IMG_ATTRS:
                del element.attrib[attr]

            # make sure the alt attribute is valid
            alt = element.get('alt')
            not_valid = ['none', 'nothing', 'image']

            if (alt is None) or alt in not_valid:
                element.set('alt', '')

    def _reformat_endnotes(self, root):
        """Insert internal link to endnote's body into the sup tag.

        :Args:
          - root: lxml node tree with the chapter content
        """
        reformat_endnotes(root)
