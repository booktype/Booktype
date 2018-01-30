import ebooklib

from lxml import etree
from ebooklib.utils import parse_html_string
from ebooklib.plugins.base import BasePlugin

from booktype.utils import config


def recursively_empty(node):
    """Recursively check if a node has no content"""
    if node.text and len(node.text.strip()) > 0:
        return False
    return all((recursively_empty(c) for c in node.iterchildren()))


class ContentCleanUpPlugin(BasePlugin):
    """
    Simple writer plugin that cleans up content. The intention is to remove not necessary
    tags, styles attributes perhaps and some other small things
    """

    def html_before_write(self, book, chapter):
        if chapter.get_type() != ebooklib.ITEM_DOCUMENT or isinstance(chapter, ebooklib.epub.EpubNav):
            return True

        tags_allowed_to_be_empty = config.get_configuration('ALLOWED_EMPTY_TAGS')
        tags_to_remove_on_cleanup = config.get_configuration('TAGS_TO_REMOVE_ON_CLEANUP')
        attrs_to_remove_on_cleanup = config.get_configuration('ATTRS_TO_REMOVE_ON_CLEANUP')
        allowed_empty_by_classes = config.get_configuration('ALLOWED_EMPTY_BY_CLASSES')

        root = parse_html_string(chapter.get_content())

        # let's remove all the tags we don't want to have on export
        # this will affect all the converters since they use the generated
        # epub as base for converting process
        for tag in tags_to_remove_on_cleanup:
            for node in root.iter(tag):
                node.drop_tree()

        # walk over all elements in the tree and remove all
        # nodes that are recursively empty
        body = root.find('body')

        for elem in body.xpath("//body//*"):
            # remove not wanted attributes
            for attr in attrs_to_remove_on_cleanup:
                if attr in elem.attrib:
                    del elem.attrib[attr]

            klasses = elem.get('class', '').split()
            allowed_by_class = any([x in allowed_empty_by_classes for x in klasses])

            if recursively_empty(elem) and elem.tag not in tags_allowed_to_be_empty and not allowed_by_class:
                # just in case if text contains spaces or tabs, because drop_tag removes only tag
                elem.text = ''
                elem.drop_tag()

        chapter.content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True
