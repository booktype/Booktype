"""
Some common functions for booki editor.
"""

import tempfile
import urllib2
from urllib import urlencode
import zipfile
import os
import simplejson
import datetime
import traceback
import time

from booki.editor import models
from booki.utils.log import logBookHistory

from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

## our own implementation of ZipFile.extract

from os import mkdir
from os.path import split, exists

def path_name(name):
    return split(name)[0]

def file_name(name):
    return split(name)[1]

def path_names(names):
    return [path_name(name) for name in names if path_name(name) != '']

def file_names(names):
    return [name for name in names if file_name(name)]

def extract(zdirname, zipfile):
    names = zipfile.namelist()

    for name in path_names(names):
        if not exists('%s/%s' % (zdirname, name)): 
            mkdir('%s/%s' % (zdirname, name))

    for name in file_names(names):
        outfile = file('%s/%s' % (zdirname, name), 'wb')
        outfile.write(zipfile.read(name))
        outfile.close()


# parse JSON

def parseJSON(js):
    import simplejson

    try:
        return simplejson.loads(js)
    except:
        return {}
    


def getChaptersFromTOC(toc):
    chapters = []

    for elem in toc:
        if elem.get('type', 'chapter') != 'booki-section':
            chapters.append( (elem.get('title', 'Missing title'), elem.get('url', 'Missing URL'), False))
        else:
            chapters.append( (elem.get('title', 'Missing title'), elem.get('url', 'Missing URL'), True))

        if elem.get('children', False) and len(elem['children']) > 0:
            chapters.extend(getChaptersFromTOC(elem['children']))

    return chapters


def importBookFromFile(user, zname, createTOC = False):
   # unzip it
    zdirname = tempfile.mkdtemp()
    zf = zipfile.ZipFile(zname)
    extract(zdirname, zf)
    zf.close()

    import logging

    logging.getLogger("booki").error("Wrote it to file %s", zname)

    # loads info.json
    data = open('%s/info.json' % zdirname, 'r').read()
    info = simplejson.loads(data)

    logging.getLogger("booki").error("Loaded json file ", extra={"info": info})

    # wtf
    bookTitle = info['metadata']['http://purl.org/dc/elements/1.1/']["title"][""][
0]

    foundAvailableName = False
    n = 0

    while not foundAvailableName:
        name = bookTitle
        if n > 0:
            name = u'%s - %d' % (bookTitle, n)

        try:
            book = models.Book.objects.get(title=name)
            n += 1
        except:
            foundAvailableName = True
            bookTitle = name

    book = createBook(user, bookTitle, status = "imported")


    # this is for Table of Contents
    n = len(info['TOC'])
    p = re.compile('\ssrc="(.*)"')
    # TOC {url, title}
    stat = models.BookStatus.objects.filter(book=book, name="imported")[0]

#    for dt in info['TOC']:
#        chapterFile = dt["url"]
#        chapterName = dt["title"]
#        urlName = slugify(chapterName)
#
###            if chapterFile.index(".") != -1:
###                chapterFile = chapterFile[:chapterFile.index(".")]
###
#        content = open('%s/%s' % (zdirname, chapterFile), 'r').read()
#
#        content = p.sub(r' src="../\1"', content)
#
#        chapter = models.Chapter(book = book,
#                                 url_title = urlName,
#                                 title = chapterName,
#                                 status = stat,
#                                 content = content,
#                                 created = datetime.datetime.now(),
#                                 modified = datetime.datetime.now())
#        chapter.save()
#
#        c = models.BookToc(book = book,
#                           name = chapterName,
#                           chapter = chapter,
#                           weight = n,
#                           typeof = 1)
#        c.save()
#        n -= 1

    # this is for Table of Contents
    # i don't want to have 200
    n = 200

    p = re.compile('\ssrc="(.*)"')

    # what if it does not have status "imported"
    stat = models.BookStatus.objects.filter(book=book, name="imported")[0]

    chapters = getChaptersFromTOC(info['TOC'])

    for inf in chapters:
        chapterName = inf[0]
        chapterFile = inf[1]
        urlName = slugify(chapterName)

        if inf[2] == True: # create section
            if createTOC:
                c = models.BookToc(book = book,
                                   name = chapterName,
                                   chapter = None,
                                   weight = n,
                                   typeof = 2)
                c.save()
                n -= 1
        else: # create chapter
            if chapterFile.index(".") != -1:
                chapterFile = chapterFile[:chapterFile.index(".")]

            # check if i can open this file at all
            content = open('%s/%s.html' % (zdirname, chapterFile), 'r').read()

            content = p.sub(r' src="../\1"', content)

            chapter = models.Chapter(book = book,
                                     url_title = urlName,
                                     title = chapterName,
                                     status = stat,
                                     content = content,
                                     created = datetime.datetime.now(),
                                     modified = datetime.datetime.now())
            chapter.save()

            if createTOC:
                c = models.BookToc(book = book,
                                   name = chapterName,
                                   chapter = chapter,
                                   weight = n,
                                   typeof = 1)
                c.save()
                n -= 1

    stat = models.BookStatus.objects.filter(book=book, name="imported")[0]

    from django.core.files import File

    for key, manifest in info['manifest'].items():
        if manifest["mimetype"] != 'text/html':
            attachmentName = manifest['url']

            if attachmentName.startswith("static/"):
                att = models.Attachment(book = book,
                                        status = stat)

                f = open('%s/%s' % (zdirname, attachmentName) , 'rb')
                att.attachment.save(file_name(attachmentName), File(f), save = False)

                att.save()

    # metadata

#    for key, value in info['metadata'].items():
#        info = models.Info(book = book, name=key)
#
#        if len(value) > 200:
#            info.value_text = value
#            info.kind = 2
#        else:
#            info.value_string = value
#            info.kind = 0
#
#        info.save()

    # delete temp files
    import shutil
    shutil.rmtree(zdirname)



def importBookFromFileTheOldWay(user, zname):
   # unzip it
    zdirname = tempfile.mkdtemp()
    zf = zipfile.ZipFile(zname)
    extract(zdirname, zf)
    zf.close()

    import logging

    logging.getLogger("booki").error("Wrote it to file %s", zname)

    # loads info.json

    data = open('%s/info.json' % zdirname, 'r').read()
    info = simplejson.loads(data)

    logging.getLogger("booki").error("Loaded json file ", extra={"info": info})

    # wtf
    bookTitle = info['metadata']['http://purl.org/dc/elements/1.1/']["title"][""][0]

    foundAvailableName = False
    n = 0

    while not foundAvailableName:
        name = bookTitle
        if n > 0:
            name = u'%s - %d' % (bookTitle, n)

        try:
            book = models.Book.objects.get(title=name)
            n += 1
        except:
            foundAvailableName = True
            bookTitle = name


    chapters = getChaptersFromTOC(info['TOC'])

    book = createBook(user, bookTitle, status = "imported")


    # this is for Table of Contents
    n = 100

    p = re.compile('\ssrc="(.*)"')

    # TOC {url, title}

    for inf in chapters:
        chapterName = inf[0]
        chapterFile = inf[1]
        urlName = slugify(chapterName)

        if not chapterFile or chapterFile == '':
            c = models.BookToc(book = book,
                               name = chapterName,
                               chapter = None,
                               weight = n,
                               typeof = 2)
            c.save()
            n -= 1
        else:
            stat = models.BookStatus.objects.filter(book=book, name="imported")[0]
            if chapterFile.index(".") != -1:
                chapterFile = chapterFile[:chapterFile.index(".")]

            content = open('%s/%s.html' % (zdirname, chapterFile), 'r').read()

            content = p.sub(r' src="../\1"', content)

            chapter = models.Chapter(book = book,
                                     url_title = urlName,
                                     title = chapterName,
                                     status = stat,
                                     content = content,
                                     created = datetime.datetime.now(),
                                     modified = datetime.datetime.now())
            chapter.save()

            typof = 1

            if inf[2]:
                typof = 0

            c = models.BookToc(book = book,
                               name = chapterName,
                               chapter = chapter,
                               weight = n,
                               typeof = typof)
            c.save()
            n -= 1



    stat = models.BookStatus.objects.filter(book=book, name="imported")[0]

    from django.core.files import File

    for key, manifest in info['manifest'].items():
        if manifest["mimetype"] != 'text/html':
            attachmentName = manifest['url']

            if attachmentName.startswith("static/"):
                att = models.Attachment(book = book,
                                        status = stat)

                f = open('%s/%s' % (zdirname, attachmentName) , 'rb')
                att.attachment.save(file_name(attachmentName), File(f), save = False)

                att.save()

    # metadata

#    for key, value in info['metadata'].items():
#        info = models.Info(book = book, name=key)
#
#        if len(value) > 200:
#            info.value_text = value
#            info.kind = 2
#        else:
#            info.value_string = value
#            info.kind = 0
#
#        info.save()

    # delete temp files
    import shutil
    shutil.rmtree(zdirname)



def importBookFromURL(user, bookURL, createTOC=False):
    """
    Imports book from the url. Creates project and book for it.
    """
    # download it
    try:
        f = urllib2.urlopen(bookURL)
        data = f.read()
        f.close()
    except urllib2.URLError, e:
        log("couldn't read %r: %s" % (bookURL, e))
        log(traceback.format_exc())
        raise

    try:
        zf = StringIO(data)
        importBookFromFile(user, zf, createTOC)
        zf.close()
    except Exception, e:
        log("couldn't make book from %r: %s" % (bookURL, e))
        log(traceback.format_exc())
        raise


def importBookFromUrl2(user, baseurl, **args):
    args['mode'] = 'zip'
    url = baseurl + "?" + urlencode(args)
    importBookFromURL(user, url, createTOC=True)



def expand_authors(book, chapter, content):
    t = template.loader.get_template_from_string('{% load booki_tags %} {% booki_authors book %}')
    con = t.render(template.Context({"content": chapter, "book": book}))
    return content.replace('##AUTHORS##', con)



def _format_metadata(book):
    metadata = {}
    # there must be language, creator, identifier and title
    #key is [ '{' namespace '}' ] name [ '[' scheme ']' ]
    key_re = re.compile(r'^(?:\{([^}]*)\})?'  # namespace
                        r'(.+)'              # keyword
                        r'(?:\[([^}]*)\])?$'  #schema
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
    lastmod = (models.BookHistory.objects.filter(book=book)
               .dates("modified", "day", order='DESC')[0]
               .strftime("%Y.%m.%d-%H.%M"))

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


def _fix_content(book, chapter):
    """fix up the html in various ways"""
    content = chapter.chapter.content
    if not content:
        return '<body><!--no content!--></body>'

    #As a special case, the ##AUTHORS## magic string gets expanded into the authors list.
    if "##AUTHORS##" in content:
        expand_authors(book, chapter, content)

    if 0:
        #for timing comparison
        p = re.compile('\ssrc="\.\.\/(.*)"')
        p2 = re.compile('\ssrc=\"\/[^\"]+\/([^"]+)\"')
        import htmlentitydefs
        exclude = ['quot', 'amp', 'apos', 'lt', 'gt']
        content = p.sub(r' src="\1"', content)
        content = p2.sub(r' src="static/\1"', content)
        for ky, val in htmlentitydefs.name2codepoint.items():
            if ky not in exclude:
                content = content.replace(unichr(val), '&%s;' % (ky, ))
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        return content

    if isinstance(content, unicode):
        content = content.encode('utf-8')

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
            log("got a wierd link: %r in %s resolves to %r, wanted start of %s" %
                (url, here, path, base + prefix))
            return url
        path = path[len(base):]
        log("turning %r into %r" % (url, path))
        return urlunsplit(('', '', path, query, frag))

    for e in tree.iter():
        src = e.get('src')
        if src is not None:
            # src attributes that point to '../static', should point to 'static'
            e.set('src', flatten(src, 'static'))

        href = e.get('href')
        if href is not None:
            e.set('href', flatten(href, ''))

    return content




def exportBook(book):
    from booki import bookizip
    import time
    starttime = time.time()
    log("hello")
    (zfile, zname) = tempfile.mkstemp()

    spine = []
    toc_top = []
    toc_current = toc_top
    waiting_for_url = []

    info = {
        "version": 1,
        "TOC": toc_top,
        "spine": spine,
        "metadata": _format_metadata(book),
        "manifest": {}
        }

    bzip = bookizip.BookiZip(zname, info=info)

    for i, chapter in enumerate(models.BookToc.objects.filter(book=book).order_by("-weight")):
        if chapter.chapter:
            # It's a real chapter! With content!
            content = _fix_content(book, chapter)

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
            ID = "s%03d_%s" % (i, slugify(title))

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

    for i, attachment in enumerate(models.Attachment.objects.filter(book=book)):
        try:
            f = open(attachment.attachment.name, "rb")
            blob = f.read()
            f.close()
        except (IOError, OSError), e:
            msg = "couldn't read attachment %s" % e
            log(msg)
            continue

        fn = os.path.basename(attachment.attachment.name.encode("utf-8"))

        ID = "att%03d_%s" % (i, fn)
        if '.' in ID:
            ID, ext = ID.rsplit('.', 1)
            mediatype = bookizip.MEDIATYPES[ext.lower()]
        else:
            mediatype = bookizip.MEDIATYPES[None]

        bzip.add_to_package(ID,
                            "static/%s" % fn,
                            blob,
                            mediatype)


    bzip.finish()
    log("export took %s seconds" % (time.time() - starttime))
    return zname
