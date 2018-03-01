# -*- coding: utf-8 -*-
import json
import datetime
import logging

from ebooklib import epub

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.views.generic import UpdateView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from braces.views import JSONResponseMixin
from booki.editor.models import Book, Chapter

from sputnik.utils import LazyEncoder

from booktype.apps.core.views import SecurityMixin
from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booktype.importer import utils as importer_utils
from booktype.importer.docx.utils import get_importer_class

from booktype.utils import config
from booktype.utils.book import check_book_availability, create_book
from booktype.utils.misc import booktype_slugify, get_file_extension, has_book_limit
from booktype.utils.security import BookSecurity

from .forms import UploadBookForm, UploadDocxFileForm


logger = logging.getLogger("booktype.importer")


class ImporterView(JSONResponseMixin, SecurityMixin, FormView):

    form_class = UploadBookForm

    def check_permissions(self, request, *args, **kwargs):
        # TODO: this should be moved to parent SecurityMixin class
        if request.user.is_superuser:
            return

        if not self.security.has_perm('account.can_upload_book'):
            raise PermissionDenied

        # if only admin import then deny user permission to upload books
        if config.get_configuration('ADMIN_IMPORT_BOOKS'):
            raise PermissionDenied

        # check if user can import more books
        if has_book_limit(request.user):
            raise PermissionDenied

    def get_default_title(self, temp_file, ext):
        book_title = _('Imported Book %(date)s') % dict(date=datetime.date.today())

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
        ext = get_file_extension(book_file.name)

        logger.debug('ImporterView::Importing file extension is "{}".'.format(ext.encode('utf8')))

        default_book_title = self.get_default_title(book_file, ext)
        book_title = form.cleaned_data.get('book_title', default_book_title)

        logger.debug('ImporterView::book_title="{}" default_book_title="{}".'.format(
            book_title.encode('utf8'), default_book_title.encode('utf8')))

        # in case book title in form is empty string
        if len(book_title) == 0:
            book_title = default_book_title

        if not check_book_availability(book_title):
            registered = Book.objects.filter(title__startswith=book_title).count()
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
            response_data = dict(errors=[ugettext('Extension not supported!')])
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
            'errors': [ugettext('Something went wrong!')],
            'infos': [],
            'warnings': []
        }
        return self.render_json_response(response_data)


class ImportToChapter(JSONResponseMixin, SecurityMixin, UpdateView):
    """
    Importer view to load content from given docx file (near future epub) into
    a single existing chapter

    This view will redirect to chapter edit screen if docx import succeed or will
    redirect to current screen user is

    """

    # TODO: Implement importing epub files into existent chapters

    model = Book
    form_class = UploadDocxFileForm
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    context_object_name = 'book'
    SECURITY_BRIDGE = BookSecurity
    json_encoder_class = LazyEncoder

    def check_permissions(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return

        if not self.security.has_perm('edit.import_to_chapter'):
            raise PermissionDenied

    def get_object(self, queryset=None):
        book = super(ImportToChapter, self).get_object(queryset)

        self.chapter = get_object_or_404(
            Chapter, book=book, pk=self.kwargs['chapter'])

        return book

    def get_form_kwargs(self):
        """Just override to avoid sending `instance` argument passed to form"""

        kwargs = super(ImportToChapter, self).get_form_kwargs()
        del kwargs['instance']

        return kwargs

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        chapter = self.chapter
        book = self.object
        chapter_file = form.cleaned_data.get('chapter_file')
        process_mode = form.cleaned_data.get('import_mode')

        # this are used to get information messages about import process
        notifier, delegate = CollectNotifier(), Delegate()
        response = {}

        # allow getting custom importer class if any
        docx = get_importer_class()(
            book, chapter, notifier=notifier, delegate=delegate, user=self.request.user)

        try:
            docx.import_file(chapter_file, **{'process_mode': process_mode})
            response['url'] = self.get_success_url()
            response['new_content'] = chapter.content
        except Exception as e:
            logger.error('ImporterToChapter::Unexpected error while importing file')
            logger.exception(e)
            notifier.errors.append(str(e))

        response['infos'] = notifier.infos
        response['warnings'] = notifier.warnings
        response['errors'] = notifier.errors

        response_data = json.dumps(response, cls=LazyEncoder)

        return HttpResponse(response_data, content_type="application/json")

    def form_invalid(self, form):
        # NOTE: perhaps send back validation errors
        response_data = {
            'infos': [], 'warnings': [],
            'errors': [ugettext('Something went wrong!')],
        }
        return self.render_json_response(response_data)

    def get_success_url(self):
        return '{}#edit/{}'.format(
            reverse('edit:editor', args=[self.object.url_title]), self.chapter.pk)
