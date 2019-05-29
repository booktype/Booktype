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

import json
import unidecode

from django.shortcuts import render_to_response, render
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django import forms
from django.contrib.auth.models import User
from django.db import transaction
from django.core import serializers

from booki.editor import models
from booktype.apps.core import views


def getVersion(book, version):
    """
    Returns object of type C{BookiVersion}. If version is None it returns latest version.

    @type book: C{booki.editor.models.Book}
    @param version: Book.

    @type version: C{string}
    @param version: Book version.

    @rtype version: C{booki.editor.models.BookVersion}
    @return: BookVersion object.

    @todo: This does not belong here. It has been moved to the right place, but we left reference here just in case.
    """

    return book.getVersion(version)


# BOOK

def export(request, bookid):
    """
    Django View. Returns BookiZip file.

    @param request: Django Request
    @param bookid: Book ID.
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(None)

    response = HttpResponse(content_type='application/zip')
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

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(version)

    bookSecurity = security.getUserSecurityForBook(request.user, book)

    hasPermission = security.canEditBook(book, bookSecurity)

    if not hasPermission:
        return views.ErrorPage(request, "errors/editing_forbidden.html", {"book": book})

    chapters = models.Chapter.objects.filter(version=book_version)

    tabs = ["chapters"]
    tabs += ["attachments"]
    tabs += ["covers"]
    tabs += ["history", "versions", "notes"]

    if bookSecurity.isAdmin():
        tabs += ["settings"]

    tabs += ["export"]

    isBrowserSupported = True
    browserMeta = request.META.get('HTTP_USER_AGENT', '')

    if browserMeta.find('MSIE') != -1:
        isBrowserSupported = False

    try:
        publish_options = settings.PUBLISH_OPTIONS
    except AttributeError:
        from booktype import constants
        publish_options = constants.PUBLISH_OPTIONS

    return render(
        request,
        'editor/edit_book.html', {
            "book": book,
            "book_version": book_version.getVersion(),
            "version": book_version,

            # this change will break older versions of template
            "statuses": [(s.name.replace(' ', '_'), s.name) for s in models.BookStatus.objects.filter(book = book)],
            "chapters": chapters,
            "security": bookSecurity,
            "is_admin": bookSecurity.isGroupAdmin() or bookSecurity.isBookAdmin() or bookSecurity.isSuperuser(),
            "is_owner": book.owner == request.user,
            "tabs": tabs,
            "is_browser_supported": isBrowserSupported,
            "publish_options": publish_options,
            "request": request
        }
    )


def thumbnail_attachment(request, bookid, attachment, version=None):
    """
    Returns image thumbnail for book attachment.

    @param request: Django Request
    @param bookid: Book ID
    @param attachment: Attachment name
    """

    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(version)

    path = '%s/%s' % (book_version.getVersion(), attachment)

    document_root = '%s/books/%s/%s' % (settings.DATA_ROOT, bookid, path)
#    document_root = '%s/static/%s/%s' % (settings.STATIC_DOC_ROOT, bookid, path)

    # should have one  "broken image" in case of error
    try:
        from PIL import Image
    except ImportError:
        import Image

    try:
        im = Image.open(document_root)
        im.thumbnail((150, 150), Image.ANTIALIAS)
    except IOError:
        im = Image.new('RGB', (150,150), "white")

    response = HttpResponse(content_type='image/jpeg')

    if im.mode != 'RGB':
        im = im.convert('RGB')

    im.save(response, "jpeg")
    return  response


# UPLOAD ATTACHMENT

@transaction.atomic
def upload_attachment(request, bookid, version=None):
    """
    Uploades attachments. Used from Upload dialog.

    @param request: Django Request
    @param bookid: Book ID
    @param version: Book version or None
    """

    import datetime

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(version)

    stat = models.BookStatus.objects.filter(book = book)[0]

    operationResult = True

    # check this for transactions
    try:
        for name, fileData in request.FILES.items():

            from booki.utils import log

            log.logBookHistory(book = book,
                               version = book_version,
                               args = {'filename': request.FILES[name].name},
                               user = request.user,
                               kind = 'attachment_upload'
                               )

            att = models.Attachment(version = book_version,
                                    # must remove this reference
                                    created = datetime.datetime.now(),
                                    book = book,
                                    status = stat)
            att.save()

            att.attachment.save(request.FILES[name].name, fileData, save = False)
            att.save()

        # TODO:
        # must write info about this to log!
    except IOError:
        operationResult = False
    except:
        oprerationResult = False

    if request.POST.get("attachmenttab", "") == "":
        return HttpResponse('<html><body><script> parent.closeAttachmentUpload();  </script></body></html>')

    if request.POST.get("attachmenttab", "") == "2":
        return HttpResponse('<html><body><script>  parent.FileBrowserDialogue.loadAttachments(); parent.FileBrowserDialogue.displayBrowseTab();  parent.FileBrowserDialogue.showUpload(); </script></body></html>')

    # should not call showAttachmentsTab, but it works for now
    if operationResult:
        return HttpResponse('<html><body><script> parent.jQuery.booki.editor.showAttachmentsTab(); parent.jQuery("#tabattachments FORM")[0].reset(); </script></body></html>')
    else:
        return HttpResponse('<html><body><script> parent.jQuery.booki.editor.showAttachmentsTab(); parent.jQuery("#tabattachments FORM")[0].reset(); alert(parent.jQuery.booki._("errorupload", "Error while uploading file!"));</script></body></html>')


def view_cover(request, bookid, cid, fname = None, version=None):
    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    try:
        cover = models.BookCover.objects.get(cid = cid)
    except models.BookCover.DoesNotExist:
        return HttpResponse(status=500)

    document_path = cover.attachment.path

    # extenstion

    import mimetypes
    mimetypes.init()

    extension = cover.filename.split('.')[-1].lower()

    if extension == 'tif':
        extension = 'tiff'

    if extension == 'jpg':
        extension = 'jpeg'

    content_type = mimetypes.types_map.get('.'+extension, 'binary/octet-stream')

    if request.GET.get('preview', '') == '1':
        try:
            from PIL import Image
        except ImportError:
            import Image

        try:
            if extension.lower() in ['pdf', 'psd', 'svg']:
                raise

            im = Image.open(cover.attachment.name)
            im.thumbnail((250, 250), Image.ANTIALIAS)
        except:
            try:
                im = Image.open('%s/editor/images/booktype-cover-%s.png' % (settings.STATIC_ROOT, extension.lower()))
                extension = 'png'
                content_type = 'image/png'
            except:
                # Not just IOError but anything else
                im = Image.open('%s/editor/images/booktype-cover-error.png' % settings.STATIC_ROOT)
                extension = 'png'
                content_type = 'image/png'

        response = HttpResponse(content_type=content_type)

        if extension.lower() in ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'bmp', 'tif']:
            if extension.upper() == 'JPG': extension = 'JPEG'
        else:
            extension = 'jpeg'

        im.save(response, extension.upper())

        return response

    try:
        data = open(document_path, 'rb').read()
    except IOError:
        return HttpResponse(status=500)

    response = HttpResponse(data, content_type=content_type)
    return response


@transaction.atomic
def upload_cover(request, bookid, version=None):
    """
    Uploades attachments. Used from Upload dialog.

    @param request: Django Request
    @param bookid: Book ID
    @param version: Book version or None
    """

    import datetime

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(version)

    stat = models.BookStatus.objects.filter(book = book)[0]

    operationResult = True

    # check this for transactions
    try:

        for name, fileData in request.FILES.items():
            if True:
                import hashlib

                h = hashlib.sha1()
                h.update(unidecode.unidecode(name))
                h.update(request.POST.get('format', ''))
                h.update(request.POST.get('license', ''))
                h.update(str(datetime.datetime.now()))

                license = models.License.objects.get(abbrevation=request.POST.get('license', ''))

                frm = request.POST.get('format', '').split(',')

                try:
                    width = int(request.POST.get('width', '0'))
                except ValueError:
                    width = 0

                try:
                    height = int(request.POST.get('height', '0'))
                except ValueError:
                    height = 0

                import unidecode

                try:
                    filename = unidecode.unidecode(request.FILES[name].name)
                except:
                    filename = ''

                title = request.POST.get('title', '').strip()[:250]

                cov = models.BookCover(book = book,
                                       user = request.user,
                                       cid = h.hexdigest(),
                                       title = title,
                                       filename = filename[:250],
                                       width = width,
                                       height = height,
                                       unit = request.POST.get('unit', 'mm'),
                                       booksize = request.POST.get('booksize', ''),
                                       cover_type = request.POST.get('type', ''),
                                       creator = request.POST.get('creator', '')[:40],
                                       license = license,
                                       notes = request.POST.get('notes', '')[:500],
                                       approved = False,
                                       is_book = 'book' in frm,
                                       is_ebook = 'ebook' in frm,
                                       is_pdf = 'pdf' in frm,
                                       created = datetime.datetime.now())
                cov.save()

                cov.attachment.save(request.FILES[name].name, fileData, save = False)
                cov.save()

                from booki.utils import log

                log.logBookHistory(book = book,
                                   version = book_version,
                                   args = {'filename': filename[:250], 'title': title, 'cid': cov.pk},
                                   user = request.user,
                                   kind = 'cover_upload'
                                   )


        # TODO:
        # must write info about this to log!
    except IOError:
        operationResult = False
        transaction.rollback()
    except:
        from booki.utils import log
        log.printStack()
        oprerationResult = False
        transaction.rollback()
    else:
        # maybe check file name now and save with new name
        transaction.commit()

    return HttpResponse('<html><body><script> parent.jQuery.booki.editor.showCovers(); </script></body></html>')


def view_books_json(request):
    """
    Returns data for Objavi.

    @param request: Django Request.

    @todo: Should be moved to booki.portal
    """

    books = models.Book.objects.filter(hidden=False).order_by("title")
    response = HttpResponse(content_type="application/json")
    json_serializer = serializers.get_serializer("json")()
    json_serializer.serialize(books, ensure_ascii=False, stream=response, fields=('title', 'url_title'))
    return response

def view_books_autocomplete(request, *args, **kwargs):
    """
    Returns data for jQuery UI autocomplete.

    @param request: Django Request.

    """

    term = request.GET.get("term", "").lower()
    book = request.GET.get("book", "").lower()

    if not book:
        books = models.Book.objects.filter(hidden=False).order_by("title")
        data = [dict(label_no_use=book.title, value=book.url_title)
                for book in books
                if not term or (term in book.title.lower() or
                                term in book.url_title)]
    else:
        chapters = models.Chapter.objects.filter(book__url_title=book)
        data = [dict(label_no_use=chapter.title, value=chapter.url_title)
                for chapter in chapters
                if not term or (term in chapter.title.lower() or
                                term in chapter.url_title)]

    return HttpResponse(json.dumps(data), "text/plain")
