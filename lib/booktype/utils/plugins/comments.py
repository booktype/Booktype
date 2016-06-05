# -*- coding: utf-8 -*-
from lxml import etree

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string


class CommentsCleanPlugin(BasePlugin):
    """Cleans out comments A-tag from chapter's content"""

    NAME = 'Comments Clean Plugin'
    OPTIONS = {}

    def __init__(self, kwargs={}):
        self.options = self.OPTIONS
        self.options.update(kwargs)

    def html_before_write(self, book, chapter):
        if not chapter.content:
            return None

        tree = parse_html_string(chapter.get_content())

        # remove comments reference bubble from the chapter content
        for commentsBubble in tree.xpath(".//a[@class='comment-link']"):
            commentsBubble.drop_tree()

        chapter.content = etree.tostring(
            tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
