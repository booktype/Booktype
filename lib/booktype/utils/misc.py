# This file is part of Booktype.
# Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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
import urllib
import urlparse

from lxml import etree, html
from ebooklib import epub
import ebooklib

from booki.editor import models

#################

from ebooklib.plugins.base import BasePlugin
from ebooklib.utils import parse_html_string


class TidyPlugin(BasePlugin):
    NAME = 'Tidy HTML'
    OPTIONS = {#'utf8': None,
               'tidy-mark': 'no',
               'drop-font-tags': 'yes',
               'uppercase-attributes': 'no',
               'uppercase-tags': 'no',
#               'anchor-as-name': 'no'
              }

    def __init__(self, extra = {}):
        self.options = dict(self.OPTIONS)
        self.options.update(extra)

    def html_after_read(self, book, chapter):
        if not chapter.content:
            return None

        from .tidy import tidy_cleanup
        print chapter.file_name
        (_, chapter.content) = tidy_cleanup(chapter.get_content(), **self.options)

        return chapter.content


    def html_before_write(self, book, chapter):
        if not chapter.content:
            return None

        from .tidy import tidy_cleanup

        (_, chapter.content) = tidy_cleanup(chapter.get_content(), **self.options)

        return chapter.content


def _convert_file_name(file_name):
    import os.path

    from booki.utils.misc import bookiSlugify
    
    name = os.path.basename(file_name)
    if name.rfind('.') != -1:
        _np = name[:name.rfind('.')]
        _ext = name[name.rfind('.'):]
        name = bookiSlugify(_np)+_ext

    name = urllib.unquote(name)
    name = name.replace(' ', '_')

    return name


class ImportPlugin(BasePlugin):
    NAME = 'Import Plugin'

    def __init__(self, remove_attributes = None):
        if remove_attributes:
            self.remove_attributes = remove_attributes
        else:
            # different kind of onmouse
            self.remove_attributes = ['class', 'style', 'id', 'onkeydown', 'onkeypress', 'onkeyup',
                                      'onclick', 'ondblclik', 'ondrag', 'ondragend', 'ondragenter',
                                      'ondragleave', 'ondragover', 'ondragstart', 'ondrop',
                                      'onmousedown', 'onmousemove', 'onmouseout', 'onmouseover',
                                      'onmouseup', 'onmousewheel', 'onscroll']


    def after_read(self, book):
        # change all the file names for images
        #   - should fix if attachment name has non ascii characters in the name
        #   - should remove the space if file name has it inside

        for att in  book.get_items_of_type(ebooklib.ITEM_IMAGE):            
            att.file_name = _convert_file_name(att.file_name)

    def html_after_read(self, book, chapter):
        import os.path
        import urlparse

        from lxml import etree 
        from ebooklib.utils import parse_html_string

        try:
            tree = parse_html_string(chapter.content)
        except:
            return

        root = tree.getroottree()

        if len(root.find('head')) != 0:
            head = tree.find('head')
            title = head.find('title')

            if title is not None:
                chapter.title = title.text        

        if len(root.find('body')) != 0:
            body = tree.find('body')

            # todo:
            # - fix <a href="">
            # - fix ....

            for _item in body.iter():
                if _item.tag == 'img':
                    _name = _item.get('src')
                    # this is not a good check
                    if _name and not _name.lower().startswith('http'): 
                        _item.set('src', 'static/%s' % _convert_file_name(_name))

                for t in self.remove_attributes:
                    if t in _item.attrib:
                        del _item.attrib[t]

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)

class LoadPlugin(BasePlugin):
    NAME = 'Load Plugin'


    def after_read(self, book):
        import os.path

        # change all the file names for images
        for att in  book.get_items_of_type(ebooklib.ITEM_IMAGE):            
            att.file_name = os.path.basename(att.file_name)

    def html_after_read(self, book, chapter):
        if not chapter.is_chapter():
            return

        from lxml import etree
        from ebooklib.utils import parse_html_string

        try:
            tree = parse_html_string(chapter.content)
        except:
            return

        root = tree.getroottree()

        if len(root.find('head')) != 0:
            head = tree.find('head')
            title = head.find('title')

            if title is not None:
                chapter.title = title.text

        chapter.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)


# THIS IS TEMPORARY PLACE AND TEMPORARY CODE

def import_book_from_file(epub_file, user, book_title=None):
    import urlparse
    import os.path
    import pprint
    import datetime
    import StringIO

    from django.utils.timezone import utc
    from django.core.files import File
    from lxml import etree 
    from ebooklib.utils import parse_html_string

    from booki.editor import models
    from booki.utils.book import createBook, checkBookAvailability
    from booki.utils.misc import bookiSlugify
    


    opts = {'plugins': [
                        TidyPlugin(),
                        ImportPlugin()
                        ]
            }
    epub_book = epub.read_epub(epub_file, opts)

    pp = pprint.PrettyPrinter(indent=4)

    chapters = {}
    toc = []

    def _parse_toc(elements):
        for _elem in elements:
            if isinstance(_elem, tuple):
                toc.append((1, _elem[0].title))
                _parse_toc(_elem[1])
            elif isinstance(_elem, epub.Section):
                pass
            elif isinstance(_elem, epub.Link):
                _u = urlparse.urlparse(_elem.href)                
                _name = urllib.unquote(os.path.basename(_u.path))

                if not _name in chapters:
                    chapters[_name] = _elem.title
                    toc.append((0, _name))

    _parse_toc(epub_book.toc)

    pp.pprint(toc)

    title = book_title or epub_book.metadata[epub.NAMESPACES['DC']]['title'][0][0]

    # must check if title already exists
    book = createBook(user, title)

    now = datetime.datetime.utcnow().replace(tzinfo=utc)

    stat = models.BookStatus.objects.filter(book=book, name="new")[0]


    for attach in  epub_book.get_items_of_type(ebooklib.ITEM_IMAGE):
        att = models.Attachment(book = book,
                                version = book.version,
                                status = stat)

        s = attach.get_content()
        f = StringIO.StringIO(s)
        f2 = File(f)
        f2.size = len(s)
        att.attachment.save(attach.file_name, f2, save=False)
        att.save()
        f.close()

    _imported = {}

    for chap in  epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Nav and Cover are not imported
        if not chap.is_chapter():
             continue

        # check if this chapter name already exists
        name = urllib.unquote(os.path.basename(chap.file_name))
        content = chap.get_body_content()

        # maybe this part has to go to the plugin
        # but you can not get title from <title>
        if chapters.has_key(name):
            name = chapters[name]
        else:
            name = _convert_file_name(name)

            if name.rfind('.') != -1:
                name = name[:name.rfind('.')]
                
            name = name.replace('.', '')

        chapter = models.Chapter(book = book,
                                 version = book.version,
                                 url_title = bookiSlugify(name),
                                 title = name,
                                 status = stat,
                                 content = content,
                                 created = now,
                                 modified = now)

        chapter.save()
        _imported[urllib.unquote(os.path.basename(chap.file_name))] = chapter

    # fix links
    for chap in  epub_book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if not chap.is_chapter():
             continue

        content = chap.get_content()

        try:
            tree = parse_html_string(content)
        except:
            pass

        root = tree.getroottree()

        if len(root.find('body')) != 0:
            body = tree.find('body')

            to_save = False

            for _item in body.iter():
                if _item.tag == 'a':
                    _href = _item.get('href')

                    if _href:
                        _u = urlparse.urlparse(_href)
                        pth = urllib.unquote(os.path.basename(_u.path))

                        if pth in _imported:
                            _name = _imported[pth].url_title

                            _u2 = urlparse.urljoin(_href, '../'+_name+'/')
                            _item.set('href', _u2)
                            to_save = True

            if to_save:
                chap.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
                _imported[urllib.unquote(os.path.basename(chap.file_name))].content = chap.content
                _imported[urllib.unquote(os.path.basename(chap.file_name))].save()

    n = len(toc)+1

    for _elem in toc:
        if _elem[0] == 1: #section
            c = models.BookToc(book = book,
                               version = book.version,
                               name = _elem[1],
                               chapter = None,
                               weight = n,
                               typeof = 2)
            c.save()        
        else: 
            if not _elem[1] in _imported:
                continue

            chap = _imported[_elem[1]]
            c = models.BookToc(book = book,
                               version = book.version,
                               name = chap.title,
                               chapter = chap,
                               weight = n,
                               typeof = 1)
            c.save()

    return book

############################################################################################################

def load_book_from_file(epub_file, user):
    from booki.editor import models

    opts = {'plugins': [
                         LoadPlugin()
                         ]
             }

    epub_book = epub.read_epub(epub_file, opts)

    import pprint
    import datetime
    import StringIO
    import os.path

    pp = pprint.PrettyPrinter(indent=4)

    pp.pprint(epub_book.toc)    

    from booki.utils.book import createBook, checkBookAvailability
    from booki.utils.misc import bookiSlugify

    title = epub_book.metadata[epub.NAMESPACES['DC']]['title'][0][0]
    lang = epub_book.metadata[epub.NAMESPACES['DC']]['language'][0][0]

    # must check the title
    book = createBook(user, title)

    now = datetime.datetime.now()

    stat = models.BookStatus.objects.filter(book=book, name="new")[0]

    n = 10

    from django.core.files import File
    from booki.utils.misc import bookiSlugify

    for _item in epub_book.get_items():
        if _item.get_type() == ebooklib.ITEM_DOCUMENT and _item.is_chapter(): # CHECK IF IT IS NOT NAV
            title = _item.title
            title_url = os.path.splitext(_item.file_name)[0]

            chapter = models.Chapter(book = book,
                                     version = book.version,
                                     url_title = title_url,
                                     title = title,
                                     status = stat,
                                     content = _item.get_content(),
                                     created = now,
                                     modified = now)
            chapter.save()
        elif _item.get_type() != ebooklib.ITEM_DOCUMENT:
            att = models.Attachment(book = book,
                                    version = book.version,
                                    status = stat)

            s = _item.get_content()
            f = StringIO.StringIO(s)
            f2 = File(f)
            f2.size = len(s)
            att.attachment.save(_item.file_name, f2, save=False)
            att.save()
            f.close()

    return


def export_book(fileName, book_version):
    import urlparse
    import os.path

    book = book_version.book

    epub_book = epub.EpubBook()

    # set basic info
    epub_book.set_identifier('booktype:%s' % book.url_title)
    epub_book.set_title(book.title)
    # set the language according to the language set
    epub_book.set_language('en')

#    epub_book.add_metadata(None, 'meta', '', {'name': 'booktype:owner_id', 'content': book_version.book.owner.username})

    # set description
    if book.description != '':
        epub_book.add_metadata('DC', 'description', book.description)

    # set license
    lic = book.license
    if lic:
        epub_book.add_metadata('DC', 'rights', lic.name)

    # set the author according to the owner
    epub_book.add_author(book.owner.first_name, role='aut', uid='author')

    toc = []
    section = []
    spine = ['nav']

    # parse and fetch only images which are inside
    embededImages = {}

    for chapter in book_version.getTOC():
        if chapter.chapter:
            c1 = epub.EpubHtml(title=chapter.chapter.title, file_name='%s.xhtml' % (chapter.chapter.url_title, ))
            cont = chapter.chapter.content

            from ebooklib.utils import parse_html_string

            try:
                tree = parse_html_string(cont.encode('utf-8'))
            except:
                pass

            for elem in tree.iter():
                if elem.tag == 'a':
                    href = elem.get('href')
                    if href and href.startswith('../'):
                        urlp = urlparse.urlparse(href)

                        fixed_href = urlp.path[3:-1] + '.xhtml'

                        if urlp.fragment:
                            fixed_href = "{}#{}".format(fixed_href, urlp.fragment)

                        elem.set('href', fixed_href)

                if elem.tag == 'img':
                    src = elem.get('src')
                    if src:
                        elem.set('src', 'static/'+src[7:])
                        embededImages[src] = True

            c1.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)

            epub_book.add_item(c1)
            spine.append(c1)

            if len(section) > 1:
                section[1].append(c1)
            else:
                toc.append(c1)
        else:
            if len(section) > 0:
                toc.append(section[:])
                section = []

            section = [epub.Section(chapter.name), []]
            # this is section

    # and what if == 0? then we have a problem
    if len(section) > 0:
        toc.append(section[:])

    for i, attachment in enumerate(models.Attachment.objects.filter(version=book_version)):
        if  not embededImages.has_key('static/'+os.path.basename(attachment.attachment.name)):
            continue

        try:
            f = open(attachment.attachment.name, "rb")
            blob = f.read()
            f.close()
        except (IOError, OSError), e:
            continue
        else:
            fn = os.path.basename(attachment.attachment.name.encode("utf-8"))
            itm = epub.EpubImage()
            itm.file_name = 'static/%s' % fn
            itm.content = blob
            epub_book.add_item(itm)

    epub_book.toc = toc
    epub_book.spine = spine
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    from ebooklib.plugins import booktype, standard

    opts = {'plugins': [#booktype.BooktypeLinks(book),
                        #booktype.BooktypeFootnotes(book),
                        TidyPlugin(),
                        standard.SyntaxPlugin()
                        ]
            }

    epub.write_epub(fileName, epub_book, opts)
