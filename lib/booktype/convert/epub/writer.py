import os
import urllib
import ebooklib

from lxml import etree
from ebooklib.epub import NAMESPACES

from .constants import STYLES_DIR
from .displayoptions import make_display_options_xml


class Writer(ebooklib.epub.EpubWriter):

    def _fix_nav_css_links(self, content):
        """
        Fix the path of the links in nav file
        """

        root = ebooklib.utils.parse_string(content)
        for element in root.iter('{%s}link' % NAMESPACES['XHTML']):
            href = urllib.unquote(element.get('href'))

            if href.startswith('../%s' % STYLES_DIR):
                file_name = os.path.basename(href)
                element.set(
                    'href', '{}/{}'.format(STYLES_DIR, file_name))

        content = etree.tostring(
            root, pretty_print=True, encoding='utf-8', xml_declaration=True)
        return content

    def _get_nav(self, item):
        content = super(Writer, self)._get_nav(item)
        return self._fix_nav_css_links(content)

    def _write_container(self):
        super(Writer, self)._write_container()

        display_options_xml = make_display_options_xml(**self.options)
        self.out.writestr(
            "META-INF/com.apple.ibooks.display-options.xml",
            display_options_xml
        )
