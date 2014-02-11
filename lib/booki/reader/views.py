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

import os
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User

from booki.editor import models
from booki.utils import pages
from django.conf import settings

# this is just temporary
def _customCSSExists(bookName):
    """
    Check if this book has custom CSS file.

    @type bookName: C{string}
    @param bookName: Unique Book ID
    @rtype: C{boolean}
    @return: Return False or True
    """
    return os.path.exists('%s/css/book.%s.css' % (settings.STATIC_ROOT, bookName))

def view_full(request, bookid, version=None):
    """
    Django View. Shows full content of book on one page. This is published version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param version: Version of the book
    """

    chapters = []

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)

    hasPermission = security.canEditBook(book, bookSecurity)

    if book.hidden and not hasPermission:
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            chapters.append({"type": "chapter",
                             "title": chapter.chapter.title,
                             "content": chapter.chapter.content,
                             "chapter": chapter.chapter})
        else:
            chapters.append({"type": "section",
                             "title": chapter.name})

    try:
        resp = render(request, 'reader/full.html', {"book": book, 
                                                    "book_version": book_version.getVersion(),
                                                    "chapters": chapters, 
                                                    "has_css": _customCSSExists(book.url_title),
                                                    "request": request})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp


def book_info(request, bookid, version=None):
    """
    Django View. Shows single page with all the Book info.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    book_history =  models.BookHistory.objects.filter(version = book_version).order_by("-modified")[:20]

    book_collaborators =  [e.values()[0] for e in models.BookHistory.objects.filter(version = book_version, kind = 2).values("user__username").distinct()]

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)
    isBookAdmin = bookSecurity.isAdmin()
    
    import sputnik
    channel_name = "/booki/book/%s/%s/" % (book.id, book_version.getVersion())
    online_users = sputnik.smembers("sputnik:channel:%s:users" % channel_name)

    book_versions = models.BookVersion.objects.filter(book=book).order_by("created")

    from django.utils.html import escape
    bookDescription = escape(book.description)

    try:
        resp = render(request, 'reader/book_info.html', {"book": book, 
                                                         "book_version": book_version.getVersion(),
                                                         "book_versions": book_versions,
                                                         "book_history": book_history, 
                                                         "book_collaborators": book_collaborators,
                                                         "has_css": _customCSSExists(book.url_title),
                                                         "is_book_admin": isBookAdmin,
                                                         "online_users": online_users,
                                                         "book_description": '<br/>'.join(bookDescription.replace('\r','').split('\n')),
                                                         "request": request})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp


def book_cover(request, bookid, version=None):
    """
    Return cover image for this book.

    @todo: It is wrong in so many different levels to serve attachments this way.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param version: Version of the book
    """

    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    return static.serve(request, book.cover.name, settings.MEDIA_ROOT)


def draft_book(request, bookid, version=None):
    """
    Django View. Shows main page for the draft version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)

    hasPermission = security.canEditBook(book, bookSecurity)

    if book.hidden and not hasPermission:
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    chapters = []
    firstChapter = None

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            if not firstChapter:
                firstChapter = chapter.chapter

            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    try:
        editingEnabled = False

        if request.user.is_authenticated() and book.version == book_version:
            editingEnabled = True

        if firstChapter:
            resp = redirect('draft_chapter', bookid = book.url_title, version=book_version.getVersion(), chapter=firstChapter.url_title) 
        else:
            resp = render(request, 'reader/draft_book.html', {"book": book, 
                                                             "book_version": book_version.getVersion(),
                                                             "chapters": chapters, 
                                                             "editing_enabled": editingEnabled,
                                                             "has_css": _customCSSExists(book.url_title),
                                                             "request": request})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp

def draft_chapter(request, bookid, chapter, version=None):
    """
    Django View. Shows chapter for the draft version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type chapter: C{string}
    @param chapter: Chapter name
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp =pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)

    hasPermission = security.canEditBook(book, bookSecurity)

    if book.hidden and not hasPermission:
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp


    chapters = []

    for chap in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chap.isChapter():
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    try:
        content = models.Chapter.objects.get(version=book_version, url_title = chapter)
    except models.Chapter.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/chapter_does_not_exist.html", {"chapter_name": chapter, "book": book})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp
    except models.Chapter.MultipleObjectsReturned:
        try:
            resp = pages.ErrorPage(request, "errors/chapter_duplicate.html", {"chapter_name": chapter, "book": book})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp
        
    try:
        editingEnabled = False

        if request.user.is_authenticated() and book.version == book_version:
            editingEnabled = True

        resp = render(request, 'reader/draft_chapter.html', {"chapter": chapter, 
                                                             "book": book, 
                                                             "book_version": book_version.getVersion(),
                                                             "chapters": chapters, 
                                                             "editing_enabled": editingEnabled,
                                                             "has_css": _customCSSExists(book.url_title),
                                                             "request": request, 
                                                             "content": content})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp
        

def book_view(request, bookid, version=None):
    """
    Django View. Shows main book page for the published version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)

    hasPermission = security.canEditBook(book, bookSecurity)

    if book.hidden and not hasPermission:
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    chapters = []
    firstChapter = None

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            if not firstChapter:
                firstChapter = chapter.chapter

            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    try:
        if firstChapter:
            resp = redirect('book_chapter', bookid = book.url_title, chapter=firstChapter.url_title) 
        else:
            resp = render(request, 'reader/book_view.html', {"book": book, 
                                                             "book_version": book_version.getVersion(),
                                                             "chapters": chapters, 
                                                             "has_css": _customCSSExists(book.url_title),
                                                             "request": request})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()

    return resp


def book_chapter(request, bookid, chapter, version=None):
    """
    Django View. Shows chapter for the published version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type chapter: C{string}
    @param chapter: Chapter name
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    from booki.utils import security
    bookSecurity = security.getUserSecurityForBook(request.user, book)

    hasPermission = security.canEditBook(book, bookSecurity)

    if book.hidden and not hasPermission:
        try:
            resp = pages.ErrorPage(request, "errors/no_permissions.html")
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    chapters = []

    for chap in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chap.isChapter():
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    try:
        content = models.Chapter.objects.get(version=book_version, url_title = chapter)
    except models.Chapter.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/chapter_does_not_exist.html", {"chapter_name": chapter, "book": book})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp
    except models.Chapter.MultipleObjectsReturned:
        try:
            resp = pages.ErrorPage(request, "errors/chapter_duplicate.html", {"chapter_name": chapter, "book": book})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

    try:
        resp = render(request, 'reader/book_chapter.html', {"chapter": chapter, 
                                                            "book": book, 
                                                            "book_version": book_version.getVersion(),
                                                            "chapters": chapters, 
                                                            "has_css": _customCSSExists(book.url_title),
                                                            "request": request, 
                                                            "content": content})
    except:
        transaction.rollback()
    else:
        transaction.commit()

    return resp

# PROJECT

def attachment(request, bookid,  attachment, version=None):
    """
    Django View. Returns content of an attachment.

    @todo: Not sure if this is even used anymore

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type attachment: C{string}
    @param attachment: Name of the attachment
    @type version: C{string}
    @param version: Version of the book
    """

    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp
        
    book_version = book.getVersion(version)

    path = '%s/%s' % (version, attachment)

    document_root = '%s/books/%s/' % (settings.DATA_ROOT, bookid)

    return static.serve(request, path, document_root)


def staticattachment(request, bookid,  attachment, version=None, chapter = None):
    """
    Django View. Returns content of an attachment.

    @todo: It is wrong in so many different levels to serve attachments this way.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type attachment: C{string}
    @param attachment: Name of the attachment
    @type version: C{string}
    @param version: Version of the book
    """

    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    path = '%s/%s' % (book_version.getVersion(), attachment)

    document_root = '%s/books/%s/' % (settings.DATA_ROOT, bookid)

    return static.serve(request, path, document_root)


@transaction.commit_manually
def edit_info(request, bookid, version=None):
    """
    Django View. 

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    if request.method == 'POST':
        book.description = request.POST.get('description', '')

        if request.FILES.has_key('cover'):
            from booki.utils import misc
            import os

            try:
                fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                book.setCover(fname)
                os.unlink(fname)
            except:
                pass

        try:
            book.save()

            resp = render(request, 'reader/edit_info_redirect.html', {"request": request,
                                                                      "book": book})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

        
    try:
        resp = render(request, 'reader/edit_info.html', {"request": request,
                                                         "book": book})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()    

    return resp


@transaction.commit_manually
def book_delete(request, bookid, version=None):
    """
    Django View. 

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        try:
            resp = pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

        return resp

    book_version = book.getVersion(version)

    if request.method == 'POST':
        title = request.POST.get('title', '')

        try:
            from booki.utils import security

            bookSecurity = security.getUserSecurityForBook(request.user, book)

            resp = render(request, 'reader/book_delete_error.html', {"request": request})

            if bookSecurity.isAdmin():
                if title.strip() == book.title.strip():
                    from booki.utils.book import removeBook
                
                    removeBook(book)

                    resp = render(request, 'reader/book_delete_redirect.html', {"request": request})
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()    

        return resp

        
    try:
        resp = render(request, 'reader/book_delete.html', {"request": request,
                                                           "book": book})
    except:
        transaction.rollback()
        raise
    else:
        transaction.commit()    

    return resp

