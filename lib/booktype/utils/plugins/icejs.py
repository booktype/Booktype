# -*- coding: utf-8 -*-
from lxml import etree

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string


def ice_cleanup(content, **kwargs):
    """
    This method removes "inserted" content and remove tags of "deleted" changes
    of the tracking engine trail. For example:

    <span class="ins">content and tag will be deleted</span> -> cause means it's not approved yet.
    <span class="del">content will be kept and tag removed</span> -> cause is previous content state.
    """

    tree = parse_html_string(content)

    # remove tags and content of inserted changes (not approved)
    spans_with_inserts = tree.xpath("//%(tag)s[contains(@class, '%(insert_class)s')]" % kwargs)
    for span in spans_with_inserts:
        span.drop_tree()

    # remove tag, but keep content of deleted changes
    spans_with_deletes = tree.xpath("//%(tag)s[contains(@class, '%(delete_class)s')]" % kwargs)
    for span in spans_with_deletes:
        span.drop_tag()

    return tree


class IceCleanPlugin(BasePlugin):
    """
    Removes icejs tags. It cleans out deleting tags and keeps inserted ones
    """

    NAME = 'IceJS Clean Plugin'
    OPTIONS = {
        'tag': 'span',
        'insert_class': 'ins',
        'delete_class': 'del'
    }

    def __init__(self, kwargs={}):
        self.options = self.OPTIONS
        self.options.update(kwargs)

    def html_before_write(self, book, chapter):
        if not chapter.content:
            return None

        tree = ice_cleanup(chapter.get_content(), **self.options)
        chapter.content = etree.tostring(
            tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
