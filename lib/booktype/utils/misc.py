
import os

from lxml import etree, html
from ebooklib import epub

from booki.editor import models


# THIS IS TEMPORARY PLACE AND TEMPORARY CODE

def export_book(fileName, book_version):

    book = book_version.book
    # START CREATING THE BOOK
    epub_book = epub.EpubBook()

    # set basic info
    epub_book.set_identifier('booktype:%s' % book.url_title)
    epub_book.set_title(book.title)
    # set the language according to the language set
    epub_book.set_language('en')

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
            c1.content=cont

            tree = html.document_fromstring(cont)
            for elem in tree.iter():
                if elem.tag == 'img':
                    src = elem.get('src')
                    if src:
                        embededImages[src] = True

            epub_book.add_item(c1)
            spine.append(c1)

            if len(section) > 1:
                section[1].append(c1)
        else:
            if len(section) > 0:
                toc.append(section[:])
                section = []

            section = [epub.Section(chapter.name), []]
            # this is section

    if len(section) > 0:
        toc.append(section[:])

    for i, attachment in enumerate(models.Attachment.objects.filter(version=book_version)):
        if  embededImages.has_key('static/'+attachment.attachment.name):
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

    opts = {'plugins': [booktype.BooktypeLinks(book),
                        booktype.BooktypeFootnotes(book),
                        standard.SyntaxPlugin()
                        ]
            }

    epub.write_epub(fileName, epub_book, opts)	    
