# -*- coding: utf-8 -*-
import os
import datetime
import logging

from ebooklib import epub

from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _

try:
    import json
except ImportError:
    from django.utils import simplejson as json

from braces.views import JSONResponseMixin
from booki.editor.models import Book

from booktype.apps.core.views import SecurityMixin
from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booktype.importer import utils as importer_utils

from booktype.utils import config
from booktype.utils.book import check_book_availability, create_book
from booktype.utils.misc import booktype_slugify

from .forms import UploadBookForm


logger = logging.getLogger("booktype.importer")


class ImporterView(JSONResponseMixin, SecurityMixin, FormView):

    form_class = UploadBookForm

    def check_permissions(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return

        if not self.security.has_perm('account.can_upload_book'):
            raise PermissionDenied

        # if only admin import then deny user permission to upload books
        if config.get_configuration('ADMIN_IMPORT_BOOKS'):
            raise PermissionDenied

        # check if user can import more books
        if Book.objects.filter(owner=self.request.user).count() >= config.get_configuration('BOOKTYPE_BOOKS_PER_USER') != -1:
            raise PermissionDenied

    def file_extension(self, filename):
        _, ext = os.path.splitext(os.path.basename(filename.lower()))
        return ext[1:]

    def get_default_title(self, temp_file, ext):
        book_title = _('Imported Book %(date)s') % {
            'date': datetime.date.today()
        }

        if ext == 'epub':
            epub_book = epub.read_epub(temp_file)
            try:
                dc_key = epub.NAMESPACES['DC']
                book_title = epub_book.metadata[dc_key]['title'][0][0]
            except Exception:
                pass

        return book_title

    def form_valid(self, form):
        logger.debug('ImporterView::form_valid')

        book_file = form.cleaned_data.get('book_file')
        ext = self.file_extension(book_file.name)

        logger.debug('ImporterView::Importing file extension is "{}".'.format(ext.encode('utf8')))

        default_book_title = self.get_default_title(book_file, ext)
        book_title = form.cleaned_data.get('book_title', default_book_title)

        logger.debug('ImporterView::book_title="{}" default_book_title="{}".'.format(
            book_title.encode('utf8'), default_book_title.encode('utf8')))

        # in case book title in form is empty string
        if len(book_title) == 0:
            book_title = default_book_title

        if not check_book_availability(book_title):
            registered = Book.objects.filter(
                title__startswith=book_title).count()
            book_title = '%s %s' % (book_title, registered)
            logger.debug('ImporterView::Checking book availability: "{}".'.format(book_title.encode('utf8')))

        book_url = booktype_slugify(book_title)
        book = create_book(self.request.user, book_title, book_url=book_url)
        logger.debug('ImporterView::Book created with url title="{}".'.format(book_url))

        # check if book will be hidden and set to book
        book.hidden = form.cleaned_data.get('hidden')
        book.save()

        notifier = CollectNotifier()
        delegate = Delegate()
        response = {}

        try:
            book_importer = importer_utils.get_importer_module(ext)
        except KeyError:
            logger.error('ImporterView::No importer for this extension')

            response_data = {
                'errors': [_('Extension not supported!')],
            }
            return self.render_json_response(response_data)

        try:
            book_importer(
                book_file, book, notifier=notifier, delegate=delegate)
            logger.debug('ImporterView::Book imported.')
            response['url'] = reverse('reader:infopage', args=[book.url_title])
        except Exception as e:
            logger.error('ImporterView::Some kind of error while importing book.')
            logger.exception(e)
            notifier.errors.append(str(e))

        response['infos'] = notifier.infos
        response['warnings'] = notifier.warnings
        response['errors'] = notifier.errors

        return self.render_json_response(response)

    def form_invalid(self, form):
        response_data = {
            'errors': [_('Something went wrong!')],
            'infos': [],
            'warnings': []
        }
        return self.render_json_response(response_data)
