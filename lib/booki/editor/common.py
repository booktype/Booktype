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


def createBook(project, bookTitle, status = "imported"):
    """
    Create book and sets status.
    """

    url_title = slugify(bookTitle)

    stat = models.ProjectStatus.objects.get(project=project, name=status)
    
    book = models.Book(project = project,
                       url_title = url_title,
                       title = bookTitle,
                       status = stat,
                       published = datetime.datetime.now())
    book.save()
    
    return book
    

def importBookFromURL(bookURL, createTOC = False):
    """ 
    Imports book from the url. Creates project and book for it.
    """

    ## there is no error checking for now

    # download it
    f = urllib2.urlopen(bookURL)
    data = f.read()

    (zfile, zname) = tempfile.mkstemp()
    os.write(zfile, data)

    # unzip it
    zdirname = tempfile.mkdtemp()
    zf = zipfile.ZipFile(zname)
    extract(zdirname, zf)
#    zf.extractall(zdirname)
    zf.close()

    # loads info.json

    data = open('%s/info.json' % zdirname, 'r').read()
    info = simplejson.loads(data)

    print info

    bookTitle = info['metadata']['title']

    try:
        project = models.Project.objects.get(name=bookTitle)
    except:
        project = createProject(bookTitle)

    foundAvailableName = False
    n = 0

    while not foundAvailableName:
        name = bookTitle
        if n > 0:
            name = u'%s - %d' % (bookTitle, n)

        try:
            book = models.Book.objects.get(project=project, title=name)
            n += 1
        except:
            foundAvailableName = True
            bookTitle = name

    book = createBook(project, bookTitle, status = "imported")

    # this is for Table of Contents
    n = len(info['TOC'])

    p = re.compile('\ssrc="(.*)"')

    for (chapterName, chapterFile) in info['TOC']:
        urlName = slugify(chapterName)

        # ignore Sections for now
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
            stat = models.ProjectStatus.objects.filter(project=project, name="imported")[0]

            content = open('%s/%s' % (zdirname, chapterFile), 'r').read()

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
        attachmentName, attachmentType = manifest[0], manifest[1]

        if attachmentName.startswith("static/"):
            att = models.Attachment(book = book, 
                                    status = stat)

            f = open('%s/%s' % (zdirname, attachmentName) , 'rb')
            att.attachment.save(file_name(attachmentName), File(f), save = False)

            att.save()

    # metadata

    for key, value in info['metadata'].items():
        info = models.Info(book = book, name=key)

        if len(value) > 200:
            info.value_text = value
            info.kind = 2
        else:
            info.value_string = value
            info.kind = 0

        info.save()

    # delete temp files
    import shutil
    shutil.rmtree(zdirname)
    os.unlink(zname)

    return


def exportBook(book):
    from booki import xhtml_utils
    (zfile, zname) = tempfile.mkstemp()

    bzip = xhtml_utils.BookiZip(zname)
    bzip.info = {}
    bzip.info["TOC"] = []
    bzip.info["metadata"] = {}
    bzip.info["spine"] = []

    # should really go through the BookTOC
    p = re.compile('\ssrc="\.\.\/(.*)"')

    for chapter in models.Chapter.objects.filter(book=book):
        bzip.info["TOC"].append([chapter.url_title, "%s.html" % chapter.url_title])
        bzip.info["spine"].append(chapter.url_title)

        # should reformat the content
        content = p.sub(r' src="\1"', chapter.content)
        
        bzip.add_to_package("%s.html" % chapter.url_title, "%s.html" % chapter.url_title, content.encode("utf-8"), "text/html")

    for attachment in models.Attachment.objects.filter(book=book):
        name = file_name(attachment.attachment.name)

        bzip.add_to_package(name,
                            "static/%s" % name,
                            open(attachment.attachment.name, "rb").read(),
                            xhtml_utils.MEDIATYPES[name[1+name.index("."):]])
                            
    for metadata in models.Info.objects.filter(book=book):
        bzip.info["metadata"][metadata.name] = metadata.getValue()


    bzip.finish()

    return zname

    
