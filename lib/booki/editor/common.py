"""
Some common functions for booki editor.
"""

import tempfile
import urllib2
import zipfile
import os
import simplejson
import datetime
import re
import logging

from booki.editor import models

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

## create project

def createProject(projectName, status = 0):
    """
    Creates project with default values. It also creates list of
    statuses for this project.
    """

    url_name = slugify(projectName)
    
    project = models.Project(url_name = url_name,
                             name = projectName,
                             status = status)

    try:
        project.save()
    except:
        return None

    # list of default statuses
    # this list should be configurable
    status_default = ["published", "not published", "imported"]
    n = len(status_default)

    for statusName in status_default:
        status = models.ProjectStatus(project=project, name=statusName, weight=n)
        status.save()
        n -= 1

    return project


def createBook(user, bookTitle, status = "imported"):
    """
    Create book and sets status.
    """

    url_title = slugify(bookTitle)

    book = models.Book(url_title = url_title,
                       title = bookTitle,
                       owner = user, 
                       published = datetime.datetime.now())

    book.save()

    status_default = ["published", "not published", "imported"]
    n = len(status_default)

    for statusName in status_default:
        status = models.BookStatus(book=book, name=statusName, weight=n)
        status.save()
        n -= 1

    book.status = models.BookStatus.objects.get(book=book, name="not published")
    book.save()
    
    return book


def getChaptersFromTOC(toc):
    chapters = []

    for elem in toc:
        if elem['type'] != 'booki-section':
            chapters.append( (elem['title'], elem['url']))

        if elem['children'] and len(elem['children']) > 0:
            chapters.extend(getChaptersFromTOC(elem['children']))

    return chapters


def importBookFromURL(user, bookURL, createTOC = False):
    """ 
    Imports book from the url. Creates project and book for it.
    """

    ## there is no error checking for now

    logging.debug("Importing book %s", bookURL)

    # download it
    f = urllib2.urlopen(bookURL)
    data = f.read()

    (zfile, zname) = tempfile.mkstemp()
    os.write(zfile, data)

    # unzip it
    zdirname = tempfile.mkdtemp()
    zf = zipfile.ZipFile(zname)
    extract(zdirname, zf)
    zf.close()

    logging.debug("Wrote it to file %s", zname)

    # loads info.json

    data = open('%s/info.json' % zdirname, 'r').read()
    info = simplejson.loads(data)

    logging.debug("Loaded json file ", extra={"info": info})

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

    book = createBook(user, bookTitle, status = "imported")

    # this is for Table of Contents
    n = 100

    p = re.compile('\ssrc="(.*)"')

    # TOC {url, title}

    stat = models.BookStatus.objects.filter(book=book, name="imported")[0]

    chapters = getChaptersFromTOC(info['TOC'])

    for inf in chapters:
        chapterName = inf[0]
        chapterFile = inf[1]
        urlName = slugify(chapterName)

        if not chapterFile or chapterFile == '':
            if createTOC:
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

            if createTOC:
                c = models.BookToc(book = book,
                                   name = chapterName,
                                   chapter = chapter,
                                   weight = n,
                                   typeof = 1)
                c.save()
                n -= 1

    stat = models.ProjectStatus.objects.filter(project=project, name="imported")[0]

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
    os.unlink(zname)

    return


def removeExtension(fileName):
    if fileName.index('.') != -1:
        return fileName[:fileName.index('.')]

    return fileName


def exportBook(book):
    from booki import xhtml_utils
    from booki import bookizip

    (zfile, zname) = tempfile.mkstemp()

    info = {
        "version": 1,
        "TOC": [],
        "spine": [],
        "metadata": {},
        "manifest": {}
        }

    bzip = bookizip.BookiZip(zname, info = info)

    # should really go through the BookTOC
    p = re.compile('\ssrc="\.\.\/(.*)"')


    ## should export only published chapters
    ## also should only post stuff from the TOC
    
    tocList = []
    childrenList = []
    unknown_n = 0

    for chapter in models.BookToc.objects.filter(book=book).order_by("-weight"):
        if chapter.chapter:
            content = p.sub(r' src="\1"', chapter.chapter.content)
            name = "%s.html" % chapter.chapter.url_title

            childrenList.append({"title": chapter.chapter.title,
                                 "url": name,
                                 "type": "chapter",
                                 "role": "text"
                                 })
            
            # blobk, metiatype, contributors, rightsholders, license
            bzip.add_to_package(removeExtension(name.encode("utf-8")), name.encode("utf-8"), content.encode("utf-8"), "text/html")
            bzip.info["spine"].append(removeExtension(name.encode("utf-8")))
        else:
            sectionName = "%s.html" % slugify(chapter.name.encode("utf-8"))

            bzip.add_to_package(removeExtension(sectionName), sectionName, "", "text/html")
            bzip.info["spine"].append(removeExtension(sectionName))

            if len(tocList) > 0:
                tocList[-1]["children"] = childrenList
            else:
                if len(childrenList) > 0:
                    unknownName = "Unknown-%d.html" % unknown_n

                    bzip.add_to_package(removeExtension(unknownName), unknownName, "", "text/html")
                    bzip.info["spine"].append(removeExtension(unknownName))

                    tocList.append({"title": "Unknown %d" % unknown_n,
                                    "url": unknownName,
                                    "type": "booki-section",
                                    "children": childrenList})
                    unknown_n += 1

            childrenList = []

            tocList.append({"title": chapter.name,
                            "url": sectionName,
                            "type": "booki-section"
                            })

        if len(tocList) > 0:
            tocList[-1]["children"] = childrenList
        else:
            if len(childrenList) > 0:
                unknownName = "Unknown-%d.html" % unknown_n
                
                bzip.add_to_package(removeExtension(unknownName), unknownName, "", "text/html")
                bzip.info["spine"].append(removeExtension(unknownName))
                
                tocList.append({"title": "Unknown %d" % unknown_n,
                                "url": unknownName,
                                "type": "booki-section",
                                "children": childrenList})
                
    bzip.info["TOC"] = tocList

    for attachment in models.Attachment.objects.filter(book=book):
        name = file_name(attachment.attachment.name)
        fn = "static/%s" % name

        bzip.add_to_package(removeExtension(name),
                            fn.encode("utf-8"),
                            open(attachment.attachment.name, "rb").read(),
                            bookizip.MEDIATYPES[name[1+name.index("."):].lower()])


    # there must be language, creator, identifier and title
    import datetime

    bzip.info["metadata"] = {"http://purl.org/dc/elements/1.1/": {
            "publisher": {
                "": ["FLOSS Manuals http://flossmanuals.net"]
                },
            "language": {
                "": ["en"]
                },
            "creator": {
                "": ["The Contributors"]
                },
            "contributor": {
                "": ["Jennifer Redman", "Bart Massey", "Alexander Pico",
                     "selena deckelmann", "Anne Gentle", "adam hyde", "Olly Betts",
                     "Jonathan Leto", "Google Inc And The Contributors",
                     "Leslie Hawthorn"]
                },
            "title": {
                "": [book.title]
                },
            "date": {
                "start": ["2009-10-23"],
                "last-modified": ["2009-10-30"]
                },
            "identifier": {
                "booki.cc": ["http://www.booki.cc/%s/%s" % (book.url_title, datetime.datetime.now().strftime("%Y.%m.%d-%H.%M"))]
                }
            }

        }

#    for metadata in models.Info.objects.filter(book=book):
#        bzip.info["metadata"][metadata.name] = metadata.getValue()


    bzip.finish()

    return zname


