# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

"""
Some common functions for booki editor.
"""
import tempfile
import urllib2
from urllib import urlencode
import zipfile
import os, sys
import datetime
import re
import logging
from cStringIO import StringIO
import traceback
import time

from booki.utils.json_wrapper import json

from lxml import etree, html

from django import template
from django.utils.translation import ugettext_lazy as _

from booki.editor import models
from booki.bookizip import get_metadata, add_metadata, DC, FM

from booki.utils.log import logBookHistory, logWarning
from booki.utils.book import createBook
from booki.utils.misc import bookiSlugify
from booki.editor.views import getVersion

from django.conf import settings

try:
    THIS_BOOKI_SERVER = settings.THIS_BOOKI_SERVER
    DEFAULT_PUBLISHER = settings.DEFAULT_PUBLISHER
except AttributeError:
    THIS_BOOKI_SERVER = os.environ.get('HTTP_HOST', 'booktype-demo.sourcefabric.org')
    DEFAULT_PUBLISHER = "Undefined"


class BookiError(Exception):
    pass

# parse JSON

def parseJSON(js):
    try:
        return json.loads(js)
    except Exception:
        return {}


def makeTitleUnique(requestedTitle):
    """If <requestedTitle> is unused, return that. Otherwise,
    return a title in the form `u'%s - %d' % (requestedTitle, n)`
    where n is the lowest non-clashing positive integer.
    """
    n = 0
    name = requestedTitle
    while True:
        titles = models.Book.objects.filter(title=name).count()
        urls = models.Book.objects.filter(url_title=bookiSlugify(name)).count()
        if not titles and not urls:
            return name
        n += 1
        name = u'%s - %d' % (requestedTitle, n)
        

def getChaptersFromTOC(toc):
    """Convert a nested bookizip TOC structure into a list of tuples
    in the form:

    (title, url, is_this_chapter_really_a_booki_section?)
    """
    chapters = []
    for elem in toc:
        chapters.append((elem.get('title', 'Missing title'),
                         elem.get('url', 'Missing URL'),
                         elem.get('type', 'chapter') == 'booki-section'))
        if elem.get('children'):
            chapters.extend(getChaptersFromTOC(elem['children']))

    return chapters


def importBookFromFile(user, zname, createTOC=False, **extraOptions):
    """Create a new book from a bookizip filename"""

    from booki.utils.log import logChapterHistory

    # unzip it
    zf = zipfile.ZipFile(zname)
    # load info.json
    info = json.loads(zf.read('info.json'))
    logWarning("Loaded json file %r" % info)

    metadata = info['metadata']
    manifest = info['manifest']
    TOC =      info['TOC']

    if extraOptions.get('book_title', None):
        bookTitle = extraOptions['book_title']
    else:
        bookTitle = get_metadata(metadata, 'title', ns=DC)[0]
    
    bookTitle = makeTitleUnique(bookTitle)
    logWarning("Chose unique book title %r" % bookTitle)

    if extraOptions.get('book_url', None):
        bookURL = extraOptions['book_url']
    else:
        bookURL = None

    book = createBook(user, bookTitle, status = "new", bookURL = bookURL)

    if extraOptions.get("hidden"):
        book.hidden = True
        book.save()

    # this is for Table of Contents
    p = re.compile('\ssrc="(.*)"')

    # what if it does not have status "new"
    stat = models.BookStatus.objects.filter(book=book, name="new")[0]

    chapters = getChaptersFromTOC(TOC)
    n = len(chapters) + 1 #is +1 necessary?
    now = datetime.datetime.now()

    for chapterName, chapterFile, is_section in chapters:
        urlName = bookiSlugify(chapterName)

        if is_section: # create section
            if createTOC:
                c = models.BookToc(book = book,
                                   version = book.version,
                                   name = chapterName,
                                   chapter = None,
                                   weight = n,
                                   typeof = 2)
                c.save()
                n -= 1
        else: # create chapter
            # check if i can open this file at all
            content = zf.read(chapterFile)

            #content = p.sub(r' src="../\1"', content)

            chapter = models.Chapter(book = book,
                                     version = book.version,
                                     url_title = urlName,
                                     title = chapterName,
                                     status = stat,
                                     content = content,
                                     created = now,
                                     modified = now)
            chapter.save()

            history = logChapterHistory(chapter = chapter,
                                        content = content,
                                        user = user,
                                        comment = "",
                                        revision = chapter.revision)
            
            if createTOC:
                c = models.BookToc(book = book,
                                   version = book.version,
                                   name = chapterName,
                                   chapter = chapter,
                                   weight = n,
                                   typeof = 1)
                c.save()
                n -= 1

    stat = models.BookStatus.objects.filter(book=book, name="new")[0]

    from django.core.files import File

    for item in manifest.values():
        if item["mimetype"] != 'text/html':
            attachmentName = item['url']

            if attachmentName.startswith("static/"):
                att = models.Attachment(book = book,
                                        version = book.version,
                                        status = stat)

                s = zf.read(attachmentName)
                f = StringIO(s)
                f2 = File(f)
                f2.size = len(s)
                att.attachment.save(os.path.basename(attachmentName), f2, save=False)
                att.save()
                f.close()

    # metadata
    for namespace in metadata:
        # namespace is something like "http://purl.org/dc/elements/1.1/" or ""
        # in the former case, preepend it to the name, in {}.
        ns = ('{%s}' % namespace if namespace else '')
        for keyword, schemes in metadata[namespace].iteritems():
            for scheme, values in schemes.iteritems():
                #schema, if it is set, describes the value's format.
                #for example, an identifier might be an ISBN.
                sc = ('{%s}' % scheme if scheme else '')
                key = "%s%s%s" % (ns, keyword, sc)
                for v in values:
                    info = models.Info(book=book, name=key)
                    if len(v) >= 2500:
                        info.value_text = v
                        info.kind = 2
                    else:
                        info.value_string = v
                        info.kind = 0
                    info.save()
    zf.close()

    return book






def importBookFromURL(user, bookURL, createTOC=False, **extraOptions):
    """
    Imports book from the url. Creates project and book for it.
    """
    # download it
    try:
        f = urllib2.urlopen(bookURL)
        data = f.read()
        f.close()
    except urllib2.URLError, e:
        logWarning("couldn't read %r: %s" % (bookURL, e))
        logWarning(traceback.format_exc())
        raise

    try:
        zf = StringIO(data)
        book = importBookFromFile(user, zf, createTOC, **extraOptions)
        zf.close()
    except Exception, e:
        logWarning("couldn't make book from %r: %s" % (bookURL, e))
        logWarning(traceback.format_exc())
        raise

    return book


def importBookFromUrl2(user, baseurl, args, **extraOptions):
    args['mode'] = 'zip'
    url = baseurl + "?" + urlencode(args)
    return importBookFromURL(user, url, createTOC=True, **extraOptions)



def expand_macro(chapter):
    try:
        t = template.loader.get_template_from_string('{% load booki_tags %} {% booki_format content %}')
        return t.render(template.Context({"content": chapter}))
    except template.TemplateSyntaxError:
        return chapter.content


def _format_metadata(book):
    metadata = {}
    # there must be language, creator, identifier and title
    #key is [ '{' namespace '}' ] name [ '[' scheme ']' ]
    key_re = re.compile(r'^(?:\{([^}]*)\})?'  # namespace
                        r'([^{]+)'              # keyword
                        r'(?:\{([^}]*)\})?$'  #schema
                        )

    for item in models.Info.objects.filter(book=book):
        key = item.name
        value = item.getValue()
        m = key_re.match(key)
        if m is None:
            keyword = key
            namespace, scheme = '', ''
        else:
            namespace, keyword, scheme = m.groups('')
        add_metadata(metadata, keyword, value, namespace, scheme)

    now = time.strftime("%Y.%m.%d-%H.%M")
    created = book.created.strftime("%Y.%m.%d-%H.%M")
    mods = models.BookHistory.objects.filter(book=book).dates("modified", "day", order='DESC')
    if not mods:
        lastmod = created
    else:
        lastmod = mods[0].strftime("%Y.%m.%d-%H.%M")

    # add some default values if values are not otherwise specified
    for namespace, keyword, scheme, value in (
        (DC, "publisher", "", DEFAULT_PUBLISHER),
        (DC, "language", "", "en"),
        (DC, "creator", "", "The Contributors"),
        (DC, "title", "", book.title),
        (DC, "date", "start", created),
        (DC, "date", "last-modified", lastmod),
        (DC, "date", "published", now),
        (DC, "identifier", "booki.cc", "http://%s/%s/%s" % (THIS_BOOKI_SERVER, book.url_title, now))
        ):
        if not get_metadata(metadata, keyword, namespace, scheme):
            add_metadata(metadata, keyword, value, namespace, scheme)

    #XXX add contributors
    return metadata


def _fix_content(book, chapter, chapter_n):
    """fix up the html in various ways"""
    content = '<div id="chapter-%d">%s</div>' % (chapter_n, chapter.chapter.content)

    # expand macros
    content = expand_macro(chapter.chapter)

    #if isinstance(content, unicode):
    #    content = content.encode('utf-8')

    tree = html.document_fromstring(content)

    base = "/%s/" % (book.url_title,)
    here = base + chapter.chapter.url_title
    from os.path import join, normpath
    from urlparse import urlsplit, urlunsplit

    def flatten(url, prefix):
        scheme, addr, path, query, frag = urlsplit(url)
        if scheme: #http, ftp, etc, ... ignore it
            return url
        path = normpath(join(here, path))
        if not path.startswith(base + prefix):
            #What is best here? make an absolute http:// link?
            #for now, ignore it.
            logWarning("got a wierd link: %r in %s resolves to %r, wanted start of %s" %
                (url, here, path, base + prefix))
            return url
        path = path[len(base):]
        logWarning("turning %r into %r" % (url, path))
        return urlunsplit(('', '', path, query, frag))

    for e in tree.iter():
        src = e.get('src')
        if src is not None:
            # src attributes that point to '../static', should point to 'static'
            e.set('src', flatten(src, 'static'))

        href = e.get('href')
        if href is not None:
            e.set('href', flatten(href, ''))

    return etree.tostring(tree, encoding='UTF-8', method='html')


def exportBook(book_version):
    from booki import bookizip
    import time
    starttime = time.time()

    (zfile, zname) = tempfile.mkstemp()

    spine = []
    toc_top = []
    toc_current = toc_top
    waiting_for_url = []

    info = {
        "version": 1,
        "TOC": toc_top,
        "spine": spine,
        "metadata": _format_metadata(book_version.book),
        "manifest": {}
        }

    bzip = bookizip.BookiZip(zname, info=info)
    chapter_n = 1

    for i, chapter in enumerate(models.BookToc.objects.filter(version=book_version).order_by("-weight")):
        if chapter.chapter:
            # It's a real chapter! With content!
            try:
                content = _fix_content(book_version.book, chapter, chapter_n)
            except:
                continue

            chapter_n += 1
            ID = "ch%03d_%s" % (i, chapter.chapter.url_title.encode('utf-8'))
            filename = ID + '.html'

            toc_current.append({"title": chapter.chapter.title,
                                "url": filename,
                                "type": "chapter",
                                "role": "text"
                                })

            # If this is the first chapter in a section, lend our url
            # to the section, which has no content and thus no url of
            # its own.  If this section was preceded by an empty
            # section, it will be waiting too, hence "while" rather
            # than "if".
            while waiting_for_url:
                section = waiting_for_url.pop()
                section["url"] = filename

            bzip.add_to_package(ID, filename, content, "text/html")
            spine.append(ID)

        else:
            #A new top level section.
            title = chapter.name.encode("utf-8")
            ID = "s%03d_%s" % (i, bookiSlugify(title))

            toc_current = []
            section = {"title": title,
                       "url": '',
                       "type": "booki-section",
                       "children": toc_current
                       }

            toc_top.append(section)
            waiting_for_url.append(section)


    #Attachments are images (and perhaps more).  They do not know
    #whether they are currently in use, or what chapter they belong
    #to, so we add them all.
    #XXX scan for img links while adding chapters, and only add those.

    for i, attachment in enumerate(models.Attachment.objects.filter(version=book_version)):
        try:
            f = open(attachment.attachment.name, "rb")
            blob = f.read()
            f.close()
        except (IOError, OSError), e:
            msg = "couldn't read attachment %s" % e
            logWarning(msg)
            continue

        fn = os.path.basename(attachment.attachment.name.encode("utf-8"))

        ID = "att%03d_%s" % (i, fn)
        if '.' in ID:
            ID, ext = ID.rsplit('.', 1)
            mediatype = bookizip.MEDIATYPES.get(ext.lower(), bookizip.MEDIATYPES[None])
        else:
            mediatype = bookizip.MEDIATYPES[None]

        bzip.add_to_package(ID,
                            "static/%s" % fn,
                            blob,
                            mediatype)


    bzip.finish()
    logWarning("export took %s seconds" % (time.time() - starttime))
    return zname
