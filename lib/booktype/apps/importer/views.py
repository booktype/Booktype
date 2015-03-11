# -*- coding: utf-8 -*-
import os
import tempfile
import datetime
import importlib

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

from braces.views import JSONResponseMixin
from booki.editor.models import Book

from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booktype.utils.book import check_book_availability, create_book
from booktype.utils.misc import (
    import_book_from_file, booktype_slugify)

from .forms import UploadForm, UploadBookForm


IMPORTER_MAP = {
    '.epub': ('booktype.importer.epub', 'import_epub'),
    '.docx': ('booktype.importer.docx', 'import_docx')
}


class ImporterView(JSONResponseMixin, FormView):
    form_class = UploadBookForm

    def get_form(self, form_class):
        request = self.request
        return form_class(data=request.POST, files=request.FILES)

    def file_extension(self, filename):
        _, ext = os.path.splitext(os.path.basename(filename))
        return ext

    def get_default_title(self, temp_file, ext):
        book_title = _('Imported Book %(date)s') % {
            'date': datetime.date.today()
        }

        if ext == '.epub':
            epub_book = epub.read_epub(temp_file)
            try:
                dc_key = epub.NAMESPACES['DC']
                book_title = epub_book.metadata[dc_key]['title'][0][0]
            except Exception:
                pass

        return book_title

    def get_importer(self, ext):
        module_path, import_func = IMPORTER_MAP[ext]
        module = importlib.import_module(module_path)
        return getattr(module, import_func)

    def form_valid(self, form):
        book_file = self.request.FILES['book_file']
        ext = self.file_extension(book_file.name)

        temp_file = tempfile.NamedTemporaryFile(
            prefix='importing-', suffix='%s' % ext, delete=False)
        temp_file = open(temp_file.name, 'wb+')

        for chunk in book_file.chunks():
            temp_file.write(chunk)
        temp_file.close()
        temp_file = temp_file.name

        default_book_title = self.get_default_title(temp_file, ext)
        book_title = form.cleaned_data.get('book_title', default_book_title)

        # in case book title in form is empty string
        if len(book_title) == 0:
            book_title = default_book_title

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
        response = {}

        try:
            book_importer = self.get_importer(ext)
        except KeyError:
            response_data = {
                'errors': [_('Extension not supported!')],
            }
            return self.render_json_response(response_data)

        try:
            book_importer(
                temp_file, book,
                notifier=notifier,
                delegate=delegate
            )
            response['url'] = reverse('reader:infopage', args=[book.url_title])
        except Exception as e:
            notifier.errors.append(str(e))

        response['infos'] = notifier.infos
        response['warnings'] = notifier.warnings
        response['errors'] = notifier.errors

        return self.render_json_response(response)

    def form_invalid(self, form):
        response_data = {
            'errors': [_('Something went wrong!')],
        }
        return self.render_json_response(response_data)


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
