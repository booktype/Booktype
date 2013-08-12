# -*- coding: utf-8 -*- 

from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.db import transaction

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
