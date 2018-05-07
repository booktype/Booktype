# This file is part of Booktype.
# Copyright (c) 2012
# Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import os
import json
import logging
import urlparse

from lxml import etree
from collections import OrderedDict

from ebooklib import epub
from ebooklib.plugins import standard
from ebooklib.utils import parse_html_string

from booki.editor import models

from booktype import constants
from booktype.utils import config
from booktype.apps.export.models import ExportSettings
from booktype.utils.misc import TidyPlugin, import_from_string

from booktype.utils.plugins.icejs import IceCleanPlugin
from booktype.utils.plugins.comments import CommentsCleanPlugin
from booktype.convert.epub.writerplugins import ContentCleanUpPlugin

from .epub import ExportEpubBook

logger = logging.getLogger('booktype.apps.export.utils')


def get_settings(book, export_format):
    """Get export settings for certain book and export format.

    :Args:
      - book (:class:`booki.editor.models.Book`: Book instance
      - export_format: Type of export format

    :Returns:
      Returns a dictionarty with settings for the certain format.
    """

    try:
        pw = ExportSettings.objects.get(book=book, typeof=export_format)

        settings_options = json.loads(pw.data)
    except ExportSettings.DoesNotExist:
        try:
            settings_options = config.get_configuration('EXPORT_SETTINGS')[export_format]
        except KeyError:
            # this might mean that we have custom instance setting and the provided `export_format`
            # was not found on it. We should try to get settings from constants
            default_settings = getattr(constants, 'EXPORT_SETTINGS')

            if export_format in default_settings:
                logger.warn(" ".join([
                    "Getting `%(f)s` settings from constants.py module.",
                    "Consider if it's worth it to add `%(f)s` config on",
                    "instance's settings."
                ]) % {"f": export_format})

                settings_options = default_settings[export_format]
            else:
                logger.error("{0} was not found in EXPORT_SETTINGS in constants.py module".format(export_format))
                raise
    except:
        settings_options = config.get_configuration('EXPORT_SETTINGS')[export_format]

    return settings_options


def get_settings_as_dictionary(book, export_format):
    return {elem['name']: elem['value'] for elem in get_settings(book, export_format)}


def set_settings(book, export_format, data):
    """Set export settings for certain book and export format.

    :Args:
      - book (:class:`booki.editor.models.Book`): Book instance
      - export_format: Type of export format
      - data: Dictionaty with new export settings

    """

    pw, created = ExportSettings.objects.get_or_create(book=book, typeof=export_format)
    pw.data = json.dumps(data)
    pw.save()


def set_booktype_metada(epub_book, book):
    """
    Set metadata to epub book. Metadata comes from Info model. There are some fields
    that need to be set different form, so we need this method

    :Args:
      - epub_book (:class:`booktype.apps.export.epub.ExportEpubBook`): Custom Epub Book object
      - metadata (:class:`booki.editor.models.Book`): Book instance

    :Returns:
      Returns an epub.ExportEpubBook instace object with metadata

    """

    # set identifiers
    isbn = 'booktype:%s' % book.url_title
    try:
        isbn = book.metadata.get(name='BKTERMS.print_isbn').value
    except:
        pass
    finally:
        if not isbn:
            isbn = 'booktype:%s' % book.url_title
    epub_book.set_identifier(isbn)

    # set epub isbn
    try:
        epub_isbn = book.metadata.get(name='BKTERMS.ebook_isbn').value
        epub_book.add_metadata('DC', 'identifier', epub_isbn, {'id': 'epub_ISBN'})
    except:
        pass

    # set main book title
    try:
        book_title = book.metadata.get(name='DC.title').value
    except:
        book_title = book.title
    epub_book.set_title(book_title, 'main')

    # set other kind of titles, {field_name: title-type}
    titles_map = {
        'BKTERMS.short_title': 'short',
        'BKTERMS.subtitle': 'subtitle'
    }

    for _t in book.metadata.filter(name__in=titles_map.keys()):
        epub_book.set_title(_t.value, titles_map.get(_t.name))

    # set the language according to the language set
    lang = 'en'
    if book.language:
        lang = book.language.abbrevation
    epub_book.set_language(lang)

    # set description
    if book.description != '':
        epub_book.add_metadata('DC', 'description', book.description)

    # set license
    lic = book.license
    if lic:
        epub_book.add_metadata('DC', 'rights', lic.name)

    # set the author according to the owner
    epub_book.add_author(book.author, role='aut', uid='author')

    # set the rest of metadata information stored in book info model
    excluded = [
        'DC.title', 'DC.title', 'DC.creator',
        'BKTERMS.print_isbn', 'BKTERMS.ebook_isbn'
    ] + titles_map.keys()

    for info in book.metadata.exclude(name__in=excluded):
        _standard, name = info.name.split('.')
        if _standard in ['DCTERMS', 'BKTERMS', 'ADD_META_TERMS']:
            # do other stuff
            epub_book.add_metadata(
                None, 'meta', info.value, {'property': '%s:%s' % (_standard.lower(), name)})
        else:
            epub_book.add_metadata(_standard, name, info.value)

    # Direction information is in old namespace. Just fetch it and include it
    # until we migrate everything to new namespace
    try:
        rtl = book.info_set.get(name='{http://booki.cc/}dir').get_value()

        epub_book.add_metadata(None, 'meta', rtl, {'property': 'bkterms:dir'})
    except:
        pass

    return epub_book


class ExportBook(object):
    """
    Base booktype export book class

    If you want to customize export process:
     - create your own `ExportBook` class inside your booktype app (not in Booktype)
     - inherit your class from this class
       (from booktype.apps.export.utils import ExportBook as CoreExportBook)
     - check that your new class has name `ExportBook`
       (class ExportBook(CoreExportBook):)
     - define path in settings to module where your class located
       (BOOKTYPE_EXPORT_CLASS_MODULE = 'appname.module')
    """

    ATTRIBUTES_GLOBAL = standard.ATTRIBUTES_GLOBAL + [
        'data-column',
        'data-gap',
        'data-valign',
        'data-id',
        'transform-data'
    ]

    DEFAULT_PLUGINS = [
        TidyPlugin(),
        standard.SyntaxPlugin()
    ]

    PREFIXES = {
        'bkterms': 'http://booktype.org/',
        'add_meta_terms': 'http://booktype.org/additional-metadata/'
    }

    def __init__(self, filename, book_version, **kwargs):
        """
        :Args:
          - filename (:class:`str`): First argument
          - book_version: (:class:`booki.editor.models.BookVersion`) BookVersion instance
        """
        self.filename = filename
        self.book_version = book_version
        self.kwargs = kwargs

        self.epub_book = None
        self.toc = None
        self.spine = None
        self.hold_chapters_urls = None
        self.embeded_images = {}
        self.attachments = models.Attachment.objects.filter(version=book_version)

        self._remove_icejs = kwargs.get('remove_icejs', True)
        self._remove_comments = kwargs.get('remove_comments', True)

        # add extra attributes_global
        self.ATTRIBUTES_GLOBAL += kwargs.get('extra_attributes_global', [])

        # add extra prefixes
        for k in kwargs.get('extra_prefixes', dict()):
            self.PREFIXES[k] = kwargs['extra_prefixes'][k]

        # for later usage
        self.kwargs = kwargs

    def _set_metadata(self):
        """
        Set metadata to the epub book

        :Args:
          - self (:class:`ExportBook`): current class instance
        """

        self.epub_book = set_booktype_metada(self.epub_book, self.book_version.book)

    def _add_prefix(self):
        """
        Add prefixes

        :Args:
          - self (:class:`ExportBook`): current class instance
        """

        for k in self.PREFIXES:
            self.epub_book.add_prefix(k, self.PREFIXES[k])

    def _chapter_content_hook(self, content):
        """
        Access to chapter's content html before any other actions.

        :Args:
          - self (:class:`ExportBook`): current class instance
          - content (:class:`unicode`): chapter content html as unicode

        :Returns:
          Updated chapter's content
        """

        return content

    def _chapter_tree_hook(self, tree):
        """
        Access to chapter's content as lxml.html.HtmlElement instance.

        :Args:
          - self (:class:`ExportBook`): current class instance
          - tree (:class:`lxml.html.HtmlElement`): chapter content as lxml.html.HtmlElement instance
        """

        pass

    def _epub_chapter_hook(self, epub_chapter):
        """
        Access to epub chapter object.

        :Args:
          - self (:class:`ExportBook`): current class instance
          - epub_chapter (:class:`ebooklib.epub.EpubHtml`): epub chapter instance
        """

        pass

    def _handle_chapter_element(self, elem):
        """
        Access to separate element from chapter's etree.

        :Args:
          - self (:class:`ExportBook`): current class instance
          - elem (:class:`elem.lxml.html.HtmlElement`): element from chapter's etree
        """

        # handle links
        if elem.tag == 'a':
            href = elem.get('href')
            if href and href.startswith('../'):
                urlp = urlparse.urlparse(href)

                url_title = urlp.path[3:-1]

                # if link on chapter on hold -> remove tag
                if url_title not in self.hold_chapters_urls:
                    fixed_href = url_title + '.xhtml'
                    if urlp.fragment:
                        fixed_href = "{}#{}".format(fixed_href, urlp.fragment)
                    elem.set('href', fixed_href)
                else:
                    elem.drop_tag()

        # handle images
        if elem.tag == 'img':
            if (elem.getparent().tag != 'div' or
                    'class' not in elem.getparent().attrib or
                    'image' not in elem.getparent().attrib['class'].split()):
                image_div = etree.Element('div', {'class': 'image'})
                elem.addprevious(image_div)
                image_div.insert(0, elem)

            image_div = elem.getparent()

            if (image_div.getparent().tag != 'div' or
                    'class' not in image_div.getparent().attrib or
                    ('group_img' not in image_div.getparent().attrib['class'].split() and
                      'wrap' not in image_div.getparent().attrib['class'].split())):
                group_img = etree.Element('div', {'class': 'group_img'})
                image_div.addprevious(group_img)
                group_img.insert(0, image_div)

            src = elem.get('src')

            if src:
                elem.set('src', 'static/' + src[7:])
                self.embeded_images[src] = True

        # remove endnotes without reference
        if elem.tag == 'ol' and elem.get('class') == 'endnotes':
            for li in elem.xpath("//li[@class='orphan-endnote']"):
                li.drop_tree()

    def _create_epub_images(self):
        """
        Create epub image objects

        :Args:
          - self (:class:`ExportBook`): current class instance
        """

        for i, attachment in enumerate(self.attachments):
            if ('static/' + os.path.basename(attachment.attachment.name)) not in self.embeded_images:
                continue

            try:
                f = open(attachment.attachment.name, "rb")
                blob = f.read()
                f.close()
            except (IOError, OSError):
                continue
            else:
                filename = os.path.basename(attachment.attachment.name.encode("utf-8"))
                itm = epub.EpubImage()
                itm.file_name = 'static/%s' % filename
                itm.content = blob
                self.epub_book.add_item(itm)

    def _create_toc(self):
        """
        Create table of contents

        :Args:
          - self (:class:`ExportBook`): current class instance
        """

        self.toc = OrderedDict()
        self.spine = ['nav']

        self.hold_chapters_urls = [i.url_title for i in self.book_version.get_hold_chapters()]

        for chapter in self.book_version.get_toc():
            if chapter.chapter:
                c1 = epub.EpubHtml(
                    title=chapter.chapter.title,
                    file_name='%s.xhtml' % (chapter.chapter.url_title, )
                )

                # hook for some extra customizations
                cont = self._chapter_content_hook(chapter.chapter.content)

                try:
                    tree = parse_html_string(cont.encode('utf-8'))
                except Exception as err:
                    logger.error('Error parsing chapter content %s' % err)
                    continue

                # hook for some extra customizations
                self._chapter_tree_hook(tree)

                for elem in tree.iter():
                    self._handle_chapter_element(elem)

                c1.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)

                # hook for some extra customizations
                self._epub_chapter_hook(c1)

                self.epub_book.add_item(c1)
                self.spine.append(c1)

                if chapter.parent:
                    self.toc[chapter.parent.id][1].append(c1)
                else:
                    if chapter.has_children():
                        self.toc[chapter.id] = [c1, []]
                    else:
                        self.toc[chapter.id] = c1
            else:
                epub_sec = epub.Section(chapter.name)

                if chapter.parent:
                    self.toc[chapter.parent.id][1].append(epub_sec)
                else:
                    self.toc[chapter.id] = [epub_sec, []]

    def _set_sections_settings(self):
        """
        Stores the sections settings inside the book metadata that would be
        used by converter scripts. Using metadata give us the advantage of being
        still generating a valid epub in case these settings are not removed.

        :Args:
          - self (:class:`ExportBook`): current class instance
        """

        from booktype.apps.convert.plugin import SectionsSettingsPlugin

        settings = {}
        count = 1
        for item in self.book_version.get_toc():
            if item.is_section() and item.has_children() and item.settings:
                key = SectionsSettingsPlugin.build_section_key(item.name, count)
                settings[key] = item.settings
                count += 1

        self.epub_book.add_metadata(
            None, 'meta', json.dumps(settings), {'property': 'bkterms:sections_settings'})

    def get_plugins(self):
        """
        Retrieves plugins that are going to be used in write process.

        Returns:
            List with instances of plugins to be used
        """

        write_plugins = self.DEFAULT_PLUGINS

        # comments reference bubble should be removed by default for now
        # TODO: we should implement a way to attach the comments to the raw epub file
        if self._remove_comments:
            write_plugins.insert(0, CommentsCleanPlugin())

        # ICEjs changes are removed by default, so to keep them in the epub
        # we need to pass remove_icejs as False in kwargs
        if self._remove_icejs:
            write_plugins.append(IceCleanPlugin())

        # let's add cleanup if enabled
        if config.get_configuration('ENABLE_CONTENT_CLEANUP_ON_EXPORT', False):
            write_plugins.append(ContentCleanUpPlugin())

        # add extra plugins
        write_plugins += self.kwargs.get('extra_plugins', [])

        return write_plugins

    def run(self):
        """
        Run export process.
        Write epub file.

        :Args:
          - self (:class:`ExportBook`): current class instance
        """
        self.epub_book = ExportEpubBook()

        self._set_metadata()
        self._add_prefix()
        self._create_toc()
        self._create_epub_images()
        self._set_sections_settings()

        self.epub_book.toc = self.toc.values()
        self.epub_book.spine = self.spine
        self.epub_book.add_item(epub.EpubNcx())
        self.epub_book.add_item(epub.EpubNav())

        standard.ATTRIBUTES_GLOBAL = self.ATTRIBUTES_GLOBAL

        epub.write_epub(
            self.filename, self.epub_book, {
                'plugins': self.get_plugins()
            })


def get_exporter_class():
    class_path = "{}.ExportBook".format(config.get_configuration('BOOKTYPE_EXPORT_CLASS_MODULE'))
    return import_from_string(class_path)
