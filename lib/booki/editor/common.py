import tempfile
import urllib2
import zipfile
import os
import simplejson
import datetime


from booki.editor import models

from django.template.defaultfilters import slugify


def createProject(projectName):
    url_name = slugify(projectName)
    
    project = models.Project(url_name = url_name[:20],
                             name = projectName,
                             status = 0)
    project.save()

    status_default = ["published", "not published", "imported"]
    n = len(status_default)

    for statusName in status_default:
        status = models.ProjectStatus(project=project, name=statusName, weight=n)
        status.save()
        n -= 1

    return project


def createBook(project, bookTitle):

    url_title = slugify(bookTitle)

    stat = models.ProjectStatus.objects.filter(project=project, name="imported")[0]
    
    book = models.Book(project = project,
                       url_title = url_title[:20],
                       title = bookTitle,
                       status = stat,
                       published = datetime.datetime.now())
    book.save()
    
    return book
    

def importBookFromURL(bookURL):
    # download it
    f = urllib2.urlopen(bookURL)
    data = f.read()

    (zfile, zname) = tempfile.mkstemp()
    os.write(zfile, data)

    # unzip it
    zdirname = tempfile.mkdtemp()
    zf = zipfile.ZipFile(zname)
    zf.extractall(zdirname)
    zf.close()

    # load info.json

    data = open('%s/info.json' % zdirname, 'r').read()
    info = simplejson.loads(data)


    print info

    bookTitle = info['metadata']['title']

    print bookTitle

    project = createProject(bookTitle)
    book = createBook(project, bookTitle)

    print project
    print book

 #   n = len(info['TOC'])
 #   print n

    for tocEntry in info['TOC']:
        print tocEntry
        chapterName = tocEntry[0]
        chapterFile = tocEntry[1]

        urlName = slugify(chapterName)

        stat = models.ProjectStatus.objects.filter(project=project, name="imported")[0]


        print '-----------------------------'
        print '%s/%s' % (zdirname, chapterFile)

        content = open('%s/%s' % (zdirname, chapterFile), 'r').read()

        chapter = models.Chapter(book = book,
                                 url_title = urlName[:20],
                                 title = chapterName,
                                 status = stat,
                                 content = content,
                                 created = datetime.datetime.now(),
                                 modified = datetime.datetime.now())
        chapter.save()
        
#        c = models.BookToc(book = book,
#                           name = chapterName,
#                           chapter = chapter,
#                           weight = n,
#                           typeof = 1)
#        c.save()
#        n -= 1
                                 

    return
