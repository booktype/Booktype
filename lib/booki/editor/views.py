from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django import forms
from django.contrib.auth.models import User
from django.db import transaction
from django.core import serializers
from booki.editor import models

import logging


def getVersion(book, version):
    """
    Returns object of type C{BookiVersion}. If version is None it returns latest version.

    @type book: C{booki.editor.models.Book}
    @param book: Booki book.
    @type version: C{booki.editor.models.BookVersion}
    @param version: Book version.

    @todo: This does not belong here. Must move to booki.utils.
    """

    book_ver = None

    if not version:
        book_ver = book.version
        #models.BookVersion.objects.filter(book=book).order_by("-created")[:1][0]
    else:
        if version.find('.') == -1:
            # what if there is more then one version with the same name ?!
            book_ver = models.BookVersion.objects.get(book=book, name=version)
        else:
            v = version.split('.')
            book_ver = models.BookVersion.objects.get(book=book, major = int(v[0]), minor = int(v[1]))

    return book_ver


# BOOK

def export(request, bookid):
    """
    Django View. Returns BookiZip file.

    @param request: Django Request
    @param bookid: Book ID. 
    """

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, None)

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % book.url_title

    # this is not good
    # should not do so much read/write in the memory

    from booki.editor import common
    
    fileName = common.exportBook(book_version)

    response.write(open(fileName, 'rb').read())

    import os
    os.unlink(fileName)

    return response

@login_required
def edit_book(request, bookid, version=None):
    """
    Django View. Default page for Booki editor.

    @param request: Django Request
    @param bookid: Book ID
    @param version: Book Version or None
    """

    from booki.utils import security

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    chapters = models.Chapter.objects.filter(version=book_version)

    tabs = ["chapters"]

    if bookSecurity.isAdmin():
        tabs += ["attachments"]

    tabs += ["history", "versions", "notes", "export"]


    return render_to_response('editor/edit_book.html', {"book": book, 
                                                        "book_version": book_version.getVersion(),
                                                        "version": book_version,
                                                        "chapters": chapters, 
                                                        "security": bookSecurity,
                                                        "is_admin": bookSecurity.isGroupAdmin() or bookSecurity.isBookAdmin() or bookSecurity.isSuperuser(),
                                                        "is_owner": book.owner == request.user,
                                                        "tabs": tabs,
                                                        "request": request})

def thumbnail_attachment(request, bookid, attachment, version=None):
    """
    Returns image thumbnail for book attachment.

    @param request: Django Request
    @param bookid: Book ID
    @param attachment: Attachment name
    """
    
    from django.views import static

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    path = '%s/%s' % (book_version.getVersion(), attachment)

    document_root = '%s/static/%s/%s' % (settings.STATIC_DOC_ROOT, bookid, path)

    # should have one  "broken image" in case of error
    import Image
    im = Image.open(document_root)
    im.thumbnail((150, 150), Image.ANTIALIAS)

    response = HttpResponse(mimetype='image/jpeg')
    im.save(response, "jpeg")
    return  response


# UPLOAD ATTACHMENT

@transaction.commit_manually
def upload_attachment(request, bookid, version=None):
    """
    Uploades attachments. Used from Upload dialog.

    @param request: Django Request
    @param bookid: Book ID
    @param version: Book version or None
    """

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)

    stat = models.BookStatus.objects.filter(book = book)[0]


    # check this for transactions

    for name, fileData in request.FILES.items():

        from booki.utils import log

        log.logBookHistory(book = book,
                           version = book_version,
                           args = {'filename': request.FILES[name].name},
                           user = request.user,
                           kind = 'attachment_upload')

        att = models.Attachment(version = book_version,
                                # must remove this reference
                                book = book,
                                status = stat)
        att.save()

        att.attachment.save(request.FILES[name].name, fileData, save = False)
        att.save()


        # TODO:
        # must write info about this to log!

        # maybe check file name now and save with new name
    transaction.commit()

    return HttpResponse('<html><body><script> parent.closeAttachmentUpload(); </script></body></html>')

def view_books_json(request):
    """
    Returns data for Objavi.
    
    @param request: Django Request.
    
    @todo: Should be moved to booki.portal 
    """
    
    books = models.Book.objects.all().order_by("title")
    response = HttpResponse(mimetype="application/json")
    json_serializer = serializers.get_serializer("json")()
    json_serializer.serialize(books, ensure_ascii=False, stream=response, fields=('title', 'url_title'))
    return response
