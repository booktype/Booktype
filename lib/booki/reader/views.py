import os

from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User

from booki.editor import models
from booki.editor.views import getVersion
from booki import settings

# this is just temporary
def _customCSSExists(bookName):
    return os.path.exists('%s/css/book.%s.css' % (settings.STATIC_DOC_ROOT, bookName))

def view_full(request, bookid, version=None):
    chapters = []

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            chapters.append({"type": "chapter",
                             "title": chapter.chapter.title,
                             "content": chapter.chapter.content,
                             "chapter": chapter.chapter})
        else:
            chapters.append({"type": "section",
                             "title": chapter.name})

    return render_to_response('reader/full.html', {"book": book, 
                                                   "book_version": book_version.getVersion(),
                                                   "chapters": chapters, 
                                                   "has_css": _customCSSExists(book.url_title),
                                                   "request": request})



def view_book(request, bookid, version=None):
    book = models.Book.objects.get(url_title__iexact=bookid)

    book_version = getVersion(book, version)

    chapters = []

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    return render_to_response('reader/book.html', {"book": book, 
                                                   "book_version": book_version.getVersion(),
                                                   "chapters": chapters, 
                                                   "has_css": _customCSSExists(book.url_title),
                                                   "request": request})

def view_chapter(request, bookid, chapter, version=None):
    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    chapters = []

    for chap in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chap.isChapter():
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    content = models.Chapter.objects.get(version=book_version, url_title = chapter)

    return render_to_response('reader/chapter.html', {"chapter": chapter, 
                                                      "book": book, 
                                                      "book_version": book_version.getVersion(),
                                                      "chapters": chapters, 
                                                      "has_css": _customCSSExists(book.url_title),
                                                      "request": request, 
                                                      "content": content})


# PROJECT

def attachment(request, bookid,  attachment, version=None):
    from booki import settings
    from django.views import static

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    path = '%s/%s' % (version, attachment)

    document_root = '%s/static/%s/' % (settings.STATIC_DOC_ROOT, bookid)

    return static.serve(request, path, document_root)


# i am pretty sure i do not need new view
def staticattachment(request, bookid,  attachment, version=None, chapter = None):
    from booki import settings
    from django.views import static

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    path = '%s/%s' % (book_version.getVersion(), attachment)

    document_root = '%s/static/%s/' % (settings.STATIC_DOC_ROOT, bookid)

    return static.serve(request, path, document_root)

