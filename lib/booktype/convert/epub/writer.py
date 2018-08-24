import os
import six
import urllib
import ebooklib
import logging

from lxml import etree
from ebooklib.epub import NAMESPACES
from ebooklib.epub import EpubNav, EpubHtml, EpubNcx, EpubCover, EpubItem, Section, Link
from ebooklib.utils import parse_string

from .constants import STYLES_DIR
from .displayoptions import make_display_options_xml

logger_epub2 = logging.getLogger("booktype.convert.epub2")


class Epub3Writer(ebooklib.epub.EpubWriter):
    """
    EPUB3 writer
    """

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
        content = super(Epub3Writer, self)._get_nav(item)
        return self._fix_nav_css_links(content)

    def _write_container(self):
        super(Epub3Writer, self)._write_container()

        display_options_xml = make_display_options_xml(**self.options)
        self.out.writestr(
            "META-INF/com.apple.ibooks.display-options.xml",
            display_options_xml
        )

    def _write_opf_metadata(self, root):
        nsmap = {'dc': NAMESPACES['DC'], 'opf': NAMESPACES['OPF']}
        nsmap.update(self.book.namespaces)

        metadata = etree.SubElement(root, 'metadata', nsmap=nsmap)

        el = etree.SubElement(metadata, 'meta', {'property': 'dcterms:modified'})
        if 'mtime' in self.options:
            mtime = self.options['mtime']
        else:
            import datetime
            mtime = datetime.datetime.now()
        el.text = mtime.strftime('%Y-%m-%dT%H:%M:%SZ')

        for ns_name, values in six.iteritems(self.book.metadata):
            if ns_name == NAMESPACES['OPF']:
                for values in values.values():
                    for v in values:
                        if 'property' in v[1] and v[1]['property'] == 'dcterms:modified':
                            continue
                        try:
                            el = etree.SubElement(metadata, 'meta', v[1])
                            if v[0]:
                                el.text = v[0]
                        except ValueError:
                            logging.error('Could not create metadata.')
            else:
                for name, values in six.iteritems(values):
                    for v in values:

                        try:
                            # remove print ISBN
                            if v[1]['id'] == 'id':
                                continue
                            elif v[1]['id'] == 'epub_ISBN':
                                v[1]['id'] = 'id'
                                # v[1]['opf:scheme'] = 'isbn'
                        except (KeyError, IndexError):
                            pass

                        try:
                            if ns_name:
                                el = etree.SubElement(metadata, '{%s}%s' % (ns_name, name), v[1])
                            else:
                                el = etree.SubElement(metadata, '%s' % name, v[1])

                            el.text = v[0]
                        except ValueError:
                            logging.error('Could not create metadata "{}".'.format(name))


class Epub2Writer(Epub3Writer):
    """
    EPUB3 writer
    """

    DEFAULT_OPTIONS = {
        'epub2_guide': True,
        'epub3_landmark': False,
        'landmark_title': 'Guide'
    }

    CHAPTER_XML = six.b(
        '''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
        </html>'''
    )

    NAV_XML = six.b(
        '''<?xml version="1.0" encoding="utf-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"/>'''
    )

    def __init__(self, *args, **kwargs):
        super(Epub2Writer, self).__init__(*args, **kwargs)

        self.book.templates['chapter'] = self.CHAPTER_XML
        self.book.templates['nav'] = self.NAV_XML

    # TODO since the _write_opf_file method was refactored in ebooklib,
    # we should update _write_opf method and override next methods:
    # - _write_opf_metadata
    # - _write_opf_manifest
    # - _write_opf_spine
    # - _write_opf_guide
    # - _write_opf_bindings
    # - _write_opf_file
    # to provide epub2 support
    def _write_opf(self):
        root = etree.Element(
            'package',
            {
                'xmlns': NAMESPACES['OPF'],
                'unique-identifier': self.book.IDENTIFIER_ID,
                'version': '2.0'
            }
        )

        # METADATA
        nsmap = {
            'dc': NAMESPACES['DC'],
            'opf': NAMESPACES['OPF']
        }
        nsmap.update(self.book.namespaces)

        metadata = etree.SubElement(root, 'metadata', nsmap=nsmap)

        for ns_name, values in six.iteritems(self.book.metadata):
            if ns_name == NAMESPACES['OPF']:
                pass
            else:
                for name, values in six.iteritems(values):
                    for v in values:

                        try:
                            # remove print ISBN
                            if v[1]['id'] == 'id':
                                continue
                            elif v[1]['id'] == 'epub_ISBN':
                                v[1]['id'] = 'id'
                                # v[1]['opf:scheme'] = 'isbn'
                        except (KeyError, IndexError):
                            pass

                        try:
                            if ns_name:
                                el = etree.SubElement(metadata, '{%s}%s' % (ns_name, name), v[1])
                            else:
                                el = etree.SubElement(metadata, '%s' % name, v[1])

                            el.text = v[0]
                        except ValueError:
                            logger_epub2.error('Could not create metadata "{}".'.format(name))

        # MANIFEST
        manifest = etree.SubElement(root, 'manifest')
        _ncx_id = None

        # mathml, scripted, svg, remote-resources, and switch
        # nav
        # cover-image

        for item in self.book.get_items():
            if not item.manifest:
                continue

            if isinstance(item, EpubNav):
                etree.SubElement(manifest, 'item', {'href': item.get_name(),
                                                    'id': item.id,
                                                    'media-type': item.media_type})
            elif isinstance(item, EpubNcx):
                _ncx_id = item.id
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type})
            elif isinstance(item, EpubCover):
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type})
            else:
                opts = {'href': item.file_name,
                        'id': item.id,
                        'media-type': item.media_type}

                if hasattr(item, 'properties') and len(item.properties) > 0:
                    opts['properties'] = ' '.join(item.properties)

                etree.SubElement(manifest, 'item', opts)

        # SPINE
        spine = etree.SubElement(root, 'spine', {'toc': _ncx_id or 'ncx'})

        for _item in self.book.spine:
            # this is for now
            # later we should be able to fetch things from tuple

            is_linear = True

            if isinstance(_item, tuple):
                item = _item[0]

                if len(_item) > 1:
                    if _item[1] == 'no':
                        is_linear = False
            else:
                item = _item

            if isinstance(item, EpubHtml):
                opts = {'idref': item.get_id()}

                if not item.is_linear or not is_linear:
                    opts['linear'] = 'no'
            elif isinstance(item, EpubItem):
                opts = {'idref': item.get_id()}

                if not item.is_linear or not is_linear:
                    opts['linear'] = 'no'
            else:
                opts = {'idref': item}

                try:
                    itm = self.book.get_item_with_id(item)

                    if not itm.is_linear or not is_linear:
                        opts['linear'] = 'no'
                except:
                    pass

            etree.SubElement(spine, 'itemref', opts)

        # GUIDE
        # - http://www.idpf.org/epub/20/spec/OPF_2.0.1_draft.htm#Section2.6

        if len(self.book.guide) > 0 and self.options.get('epub2_guide'):
            guide = etree.SubElement(root, 'guide', {})

            for item in self.book.guide:
                _href = item.get('href', '')
                _title = item.get('title', '')

                if 'item' in item:
                    chap = item.get('item')
                    if chap:
                        _href = chap.file_name
                        _title = chap.title

                if _title is None:
                    _title = ''

                etree.SubElement(guide, 'reference', {'type': item.get('type', ''),
                                                      'title': _title,
                                                      'href': _href})

        if len(self.book.bindings) > 0:
            bindings = etree.SubElement(root, 'bindings', {})

            for item in self.book.bindings:
                etree.SubElement(bindings, 'mediaType', item)

        tree_str = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)

        self.out.writestr('%s/content.opf' % self.book.FOLDER_NAME, tree_str)

    def _get_nav(self, item):
        # just a basic navigation for now
        ncx = parse_string(self.book.get_template('nav'))
        root = ncx.getroot()
        root.set('lang', self.book.language)
        root.attrib['{%s}lang' % NAMESPACES['XML']] = self.book.language
        nav_dir_name = os.path.dirname(item.file_name)
        head = etree.SubElement(root, 'head')
        title = etree.SubElement(head, 'title')
        title.text = self.book.title

        # for now this just handles css files and ignores others
        for _link in item.links:
            _lnk = etree.SubElement(head, 'link', {"href": _link.get('href', ''),
                                                   "rel": "stylesheet", "type": "text/css"})

        body = etree.SubElement(root, 'body')
        nav = etree.SubElement(body, 'div', {'id': 'id'})
        content_title = etree.SubElement(nav, 'h2')
        content_title.text = self.book.title

        def _create_section(itm, items):
            ol = etree.SubElement(itm, 'ol')
            for item in items:
                if isinstance(item, tuple) or isinstance(item, list):
                    li = etree.SubElement(ol, 'li')
                    if isinstance(item[0], EpubHtml):
                        a = etree.SubElement(li, 'a', {'href': os.path.relpath(item[0].file_name, nav_dir_name)})
                    elif isinstance(item[0], Section) and item[0].href != '':
                        a = etree.SubElement(li, 'a', {'href': os.path.relpath(item[0].href, nav_dir_name)})
                    elif isinstance(item[0], Link):
                        a = etree.SubElement(li, 'a', {'href': os.path.relpath(item[0].href, nav_dir_name)})
                    else:
                        a = etree.SubElement(li, 'span')
                    a.text = item[0].title

                    _create_section(li, item[1])

                elif isinstance(item, Link):
                    li = etree.SubElement(ol, 'li')
                    a = etree.SubElement(li, 'a', {'href': os.path.relpath(item.href, nav_dir_name)})
                    a.text = item.title
                elif isinstance(item, EpubHtml):
                    li = etree.SubElement(ol, 'li')

                    a = etree.SubElement(li, 'a', {'href': os.path.relpath(item.file_name, nav_dir_name)})
                    a.text = item.title

        _create_section(nav, self.book.toc)

        # LANDMARKS / GUIDE
        # - http://www.idpf.org/epub/30/spec/epub30-contentdocs.html#sec-xhtml-nav-def-types-landmarks

        if len(self.book.guide) > 0 and self.options.get('epub3_landmark'):

            # Epub2 guide types do not map completely to epub3 landmark types.
            guide_to_landscape_map = {
                'notes': 'rearnotes',
                'text': 'bodymatter'
            }

            guide_nav = etree.SubElement(body, 'nav', {'{%s}type' % NAMESPACES['EPUB']: 'landmarks'})

            guide_content_title = etree.SubElement(guide_nav, 'h2')
            guide_content_title.text = self.options.get('landmark_title', 'Guide')

            guild_ol = etree.SubElement(guide_nav, 'ol')

            for elem in self.book.guide:
                li_item = etree.SubElement(guild_ol, 'li')

                _href = elem.get('href', '')
                _title = elem.get('title', '')

                if 'item' in elem:
                    chap = elem.get('item', None)
                    if chap:
                        _href = chap.file_name
                        _title = chap.title

                guide_type = elem.get('type', '')
                a_item = etree.SubElement(
                    li_item,
                    'a',
                    {
                        '{%s}type' % NAMESPACES['EPUB']: guide_to_landscape_map.get(guide_type, guide_type),
                        'href': os.path.relpath(_href, nav_dir_name)
                    }
                )
                a_item.text = _title

        tree_str = etree.tostring(ncx, pretty_print=True, encoding='utf-8', xml_declaration=True)

        return self._fix_nav_css_links(tree_str)

    def _write_items(self):
        for item in self.book.get_items():
            if isinstance(item, EpubNcx):
                self.out.writestr('%s/%s' % (self.book.FOLDER_NAME, item.file_name), self._get_ncx())
            elif isinstance(item, EpubNav):
                self.out.writestr('%s/%s' % (self.book.FOLDER_NAME, item.file_name), self._get_nav(item))
            elif item.manifest:
                self.out.writestr('%s/%s' % (self.book.FOLDER_NAME, item.file_name), item.get_content())
            else:
                self.out.writestr('%s' % item.file_name, item.get_content())
