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
import urlparse

from lxml import etree
from collections import OrderedDict

from ebooklib import epub
from ebooklib.plugins import standard
from ebooklib.utils import parse_html_string

from booki.editor import models
from booktype.utils import config
from booktype.apps.export.models import ExportSettings
from booktype.utils.misc import TidyPlugin

from .epub import ExportEpubBook


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
        settings_options = config.get_configuration('EXPORT_SETTINGS')[export_format]
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
    try:
        isbn = book.metadata.get(name='BKTERMS.print_isbn').value
    except:
        isbn = 'booktype:%s' % book.url_title
    epub_book.set_identifier(isbn)

    # set epub isbn
    try:
        epub_isbn = book.metadata.get(name='BKTERMS.epub_isbn').value
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
        'BKTERMS.print_isbn', 'BKTERMS.epub_isbn'
    ] + titles_map.keys()

    for info in book.metadata.exclude(name__in=excluded):
        _standard, name = info.name.split('.')
        if _standard in ['DCTERMS', 'BKTERMS']:
            # do other stuff
            epub_book.add_metadata(
                None, 'meta', info.value, {'property': '%s:%s' % (_standard.lower(), name)})
        else:
            epub_book.add_metadata(_standard, name, info.value)

    return epub_book


def export_book(filename, book_version):
    book = book_version.book
    epub_book = ExportEpubBook()

    # set metadata to the epub book
    epub_book = set_booktype_metada(epub_book, book)
    epub_book.add_prefix('bkterms', 'http://booktype.org/')

    toc = OrderedDict()
    spine = ['nav']

    # parse and fetch only images which are inside
    embeded_images = {}

    hold_chapters_urls = [i.url_title for i in book_version.get_hold_chapters()]

    for chapter in book_version.get_toc():
        if chapter.chapter:
            c1 = epub.EpubHtml(
                title=chapter.chapter.title,
                file_name='%s.xhtml' % (chapter.chapter.url_title, )
            )
            cont = chapter.chapter.content

            try:
                tree = parse_html_string(cont.encode('utf-8'))
            except:
                pass

            for elem in tree.iter():
                if elem.tag == 'a':
                    href = elem.get('href')
                    if href and href.startswith('../'):
                        urlp = urlparse.urlparse(href)

                        url_title = urlp.path[3:-1]

                        # if link on chapter on hold -> remove tag
                        if url_title not in hold_chapters_urls:
                            fixed_href = url_title + '.xhtml'
                            if urlp.fragment:
                                fixed_href = "{}#{}".format(fixed_href, urlp.fragment)
                            elem.set('href', fixed_href)
                        else:
                            elem.drop_tag()

                if elem.tag == 'img':
                    src = elem.get('src')
                    if src:
                        elem.set('src', 'static/' + src[7:])
                        embeded_images[src] = True

            c1.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)

            epub_book.add_item(c1)
            spine.append(c1)

            if chapter.parent:
                toc[chapter.parent.id][1].append(c1)
            else:
                if chapter.has_children():
                    toc[chapter.id] = [c1, []]
                else:
                    toc[chapter.id] = c1
        else:
            epub_sec = epub.Section(chapter.name)
            if chapter.parent:
                toc[chapter.parent.id][1].append(epub_sec)
            else:
                toc[chapter.id] = [epub_sec, []]

    for i, attachment in enumerate(models.Attachment.objects.filter(version=book_version)):
        if ('static/' + os.path.basename(attachment.attachment.name)) not in embeded_images:
            continue

        try:
            f = open(attachment.attachment.name, "rb")
            blob = f.read()
            f.close()
        except (IOError, OSError):
            continue
        else:
            fn = os.path.basename(attachment.attachment.name.encode("utf-8"))
            itm = epub.EpubImage()
            itm.file_name = 'static/%s' % fn
            itm.content = blob
            epub_book.add_item(itm)

    epub_book.toc = toc.values()
    epub_book.spine = spine
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    opts = {'plugins': [TidyPlugin(), standard.SyntaxPlugin()]}
    epub.write_epub(filename, epub_book, opts)
