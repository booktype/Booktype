# -*- coding: utf-8 -*- 

from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

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
