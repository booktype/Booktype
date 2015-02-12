# -*- coding: utf-8 -*-
import tempfile
import datetime

from ebooklib import epub

from django.db import transaction
from django.shortcuts import render
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, HttpResponseRedirect

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from booki.editor.models import Book
from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booktype.utils.book import check_book_availability, create_book
from booktype.utils.misc import (
    import_book_from_file, booktype_slugify)

from .forms import UploadForm, UploadBookForm


class ImporterView(FormView):
    form_class = UploadBookForm

    def get_form(self, form_class):
        request = self.request
        return form_class(data=request.POST, files=request.FILES)

    def form_valid(self, form):
        import booktype.importer.epub

        book_file = self.request.FILES['book_file']
        book_title = form.cleaned_data.get('book_title', None)
        if not book_title:
            pass

        temp_file = tempfile.NamedTemporaryFile(
            prefix="importing-", suffix=".epub", delete=False)
        temp_file = open(temp_file.name, 'wb+')

        for chunk in book_file.chunks():
            temp_file.write(chunk)
        temp_file.close()
        temp_file = temp_file.name

        epub_book = epub.read_epub(temp_file)
        try:
            dc_key = epub.NAMESPACES['DC']
            epub_book_name = epub_book.metadata[dc_key]['title'][0][0]
        except Exception:
            epub_book_name = _('Imported Book %(date)s') % {
                'date': datetime.date.today()
            }

        book_title = form.cleaned_data.get('book_title', epub_book_name)
        if len(book_title) == 0:
            book_title = epub_book_name

        if not check_book_availability(book_title):
            registered = Book.objects.filter(
                title__startswith=book_title).count()
            book_title = '%s %s' % (book_title, registered)

        book_url = booktype_slugify(book_title)
        book = create_book(
            self.request.user, book_title, book_url=book_url)

        # check if book will be hidden and set to book
        book_hidden = form.cleaned_data.get('hidden')
        if book_hidden:
            book.hidden = book_hidden
            book.save()

        notifier = CollectNotifier()
        delegate = Delegate()
        reponse = {}

        try:
            booktype.importer.epub.import_epub(
                temp_file, book,
                notifier=notifier,
                delegate=delegate
            )
            reponse['url'] = reverse('reader:infopage', args=[book.url_title])
        except Exception as e:
            notifier.errors.append(str(e))

        reponse['infos'] = notifier.infos
        reponse['warnings'] = notifier.warnings
        reponse['errors'] = notifier.errors

        return HttpResponse(
            json.dumps(reponse), mimetype='application/json')

    def form_invalid(self, form):
        response_data = {
            "errors": [_('Something went wrong!')],
        }

        return HttpResponse(
            json.dumps(response_data), mimetype='application/json')


def frontpage(request):
    if request.method == 'POST':  # If the form has been submitted...
        # A form bound to the POST data
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():  # All validation rules pass

            fil = request.FILES['file']

            f = open('/tmp/acika.epub', 'wb+')
            for chunk in fil.chunks():
                f.write(chunk)
            f.close()

            try:
                title = None
                if form.cleaned_data['title'].strip() != '':
                    title = form.cleaned_data['title']

                book = import_book_from_file(
                    '/tmp/acika.epub', request.user, book_title=title)
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()

            from django.core.urlresolvers import reverse

            url = reverse('reader:infopage', kwargs={'bookid': book.url_title})
            res = HttpResponseRedirect(url)  # Redirect after POST

            return res
    else:
        form = UploadForm()  # An unbound form

    resp = render(request, 'importer/frontpage.html', {
        'request': request,
        'form': form
    })
    return resp


def upload_progress(request):
    """
    Used by Ajax calls
    Return the upload progress and total length values
    """
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        data = cache.get(cache_key)
        return HttpResponse(json.dumps(data))
