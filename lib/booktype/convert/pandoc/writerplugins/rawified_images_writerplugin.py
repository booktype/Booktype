# -*- coding: utf-8 -*-
import ebooklib
import logging

from lxml import etree
from ebooklib.plugins.base import BasePlugin

logger = logging.getLogger("booktype.convert.epub")


class RawifiedImagesWriterPlugin(BasePlugin):
    """
    Removes image editor required data from html.
    """

    def html_before_write(self, book, item):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            return True

        if isinstance(item, ebooklib.epub.EpubNav):
            return True

        root = ebooklib.utils.parse_html_string(item.content)

        for elem in root.iter('img'):
            div_image = elem.getparent()
            div_group_img = div_image.getparent()

            # delete redundant attrs
            if elem.get('style'):
                del elem.attrib['style']

            if elem.get('transform-data'):
                del elem.attrib['transform-data']

            if elem.get('width'):
                del elem.attrib['width']

            if elem.get('height'):
                del elem.attrib['height']

            if div_image.get('style'):
                del div_image.attrib['style']

            # find old captions using p.caption_small
            for p_caption in div_group_img.xpath('p[contains(@class,"caption_small")]'):
                if p_caption.get('style'):
                    del p_caption.attrib['style']

                if p_caption.get('class'):
                    del p_caption.attrib['class']

                # set new class and change tag
                p_caption.set('class', 'caption_small')
                p_caption.tag = 'div'

            # remove style from caption
            for div_caption in div_group_img.xpath('div[contains(@class,"caption_small")]'):
                if div_caption.get('style'):
                    del div_caption.attrib['style']

        item.content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True
