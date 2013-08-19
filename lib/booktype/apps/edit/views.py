# -*- coding: utf-8 -*- 

import datetime

from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings

from booki.utils import log
from booki.editor import models

def getTOCForBook(version):
    results = []
    for chap in version.getTOC():
        # is it a section or chapter?
        if chap.chapter:
            results.append((chap.chapter.id,
                            chap.chapter.title,
                            chap.chapter.url_title,
                            chap.typeof,
                            chap.chapter.status.id))
        else:
            results.append(('s%s' % chap.id, chap.name, chap.name, chap.typeof))
    return results


@login_required
@transaction.commit_manually
def upload_attachment(request, bookid, version=None):
    import json
    import datetime

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(version)

    stat = models.BookStatus.objects.filter(book = book)[0]

    operationResult = True

    # check this for transactions
    try:
        fileData = request.FILES['files[]']
        att = models.Attachment(version = book_version,
                                # must remove this reference
                                created = datetime.datetime.now(),
                                book = book,
                                status = stat)
        att.save()
        att.attachment.save(fileData.name, fileData, save = False)
        att.save()

        # TODO:
        # must write info about this to log!
    # except IOError:
    #     operationResult = False
    #     transaction.rollback()
    except:
        oprerationResult = False
        transaction.rollback()
    else:
       # maybe check file name now and save with new name
       transaction.commit()


    response_data = {"files":[{"url":"http://127.0.0.1/",
                                "thumbnail_url":"http://127.0.0.1/",
                                "name":"boot.png",
                                "type":"image/png",
                                "size":172728,
                                "delete_url":"",
                                "delete_type":"DELETE"}]}

    return HttpResponse(json.dumps(response_data), mimetype="application/json")


@login_required
@transaction.commit_manually
def upload_cover(request, bookid, version=None):
    import json
    import datetime

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.getVersion(version)

    operationResult = True

    # check this for transactions
    try:
        fileData = request.FILES['files[]']

        title = request.POST.get('title', '')

        import hashlib

        h = hashlib.sha1()
        h.update(fileData.name)
        h.update(title)
        h.update(str(datetime.datetime.now()))

        license = models.License.objects.get(abbrevation=request.POST.get('license', ''))

        try:
            filename = unidecode.unidecode(fileData.name)
        except:
            filename = ''

        cov = models.BookCover(book = book,
                               user = request.user,
                               cid = h.hexdigest(),
                               title = title,
                               filename = filename[:250],
                               width = 0,
                               height = 0,
                               unit = request.POST.get('unit', 'mm'),
                               booksize = request.POST.get('booksize', ''),
                               cover_type = request.POST.get('type', ''),
                               creator = request.POST.get('creator', '')[:40],
                               license = license,
                               notes = request.POST.get('notes', '')[:500],
                               approved = False,
                               is_book = False,
                               is_ebook = True,
                               is_pdf = False,
                               created = datetime.datetime.now())
        cov.save()
        
        cov.attachment.save(fileData.name, fileData, save = False)
        cov.save()

        # TODO:
        # must write info about this to log!
    # except IOError:
    #     operationResult = False
    #     transaction.rollback()
    except:
        oprerationResult = False
        transaction.rollback()
    else:
       # maybe check file name now and save with new name
       transaction.commit()


    response_data = {"files":[{"url":"http://127.0.0.1/",
                                "thumbnail_url":"http://127.0.0.1/",
                                "name":"boot.png",
                                "type":"image/png",
                                "size":172728,
                                "delete_url":"",
                                "delete_type":"DELETE"}]}

    return HttpResponse(json.dumps(response_data), mimetype="application/json")

@login_required
def cover(request, bookid, cid, fname = None, version=None):
    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    try:
        cover = models.BookCover.objects.get(cid = cid)
    except models.BookCover.DoesNotExist:
        return HttpResponse(status=500)

    document_path = '%s/book_covers/%s' % (settings.DATA_ROOT, cover.id)
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
            im.thumbnail((300, 200), Image.ANTIALIAS)
        except:
            try:
                im = Image.open('%s/editor/images/booktype-cover-%s.png' % (settings.SITE_STATIC_ROOT, extension.lower()))
                extension = 'png'
                content_type = 'image/png'
            except:
                # Not just IOError but anything else
                im = Image.open('%s/editor/images/booktype-cover-error.png' % settings.SITE_STATIC_ROOT)
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

@login_required
def edit(request, bookid):
    book = models.Book.objects.get(url_title__iexact=bookid)

    toc = getTOCForBook(book.getVersion(None))
    book_version = book.getVersion(None)
    book_version = '1.0'
    resp =  render(request, 'edit/book_edit.html', {'request': request,
    		                                        'chapters': toc,
    		   										'book': book,
    		   										'book_version': book_version})

    return resp
