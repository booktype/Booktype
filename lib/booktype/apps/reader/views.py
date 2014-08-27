# This file is part of Booktype.
# Copyright (c) 2014 Helmy Giacoman <helmy.giacoman@sourcefabric.org>
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

from django.views import static
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, Http404
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, DeleteView, UpdateView

from braces.views import LoginRequiredMixin

from booki.utils import security
from booktype.utils import misc
from booktype.utils.book import remove_book
from booktype.apps.core.views import BasePageView
from booki.editor.models import Book, BookHistory, BookToc, Chapter

from .forms import EditBookInfoForm

class BaseReaderView(object):
    """
    Base Reader View Class with the common attributes
    """

    model = Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    context_object_name = 'book'
    not_found = False

    def get(self, request, *args, **kwargs):
        try:
            return super(BaseReaderView, self).get(request, *args, **kwargs)
        except Http404:
            self.not_found = True
            context = dict(
                not_found_object=_("Book"),
                object_name=self.kwargs['bookid']
            )
            return self.render_to_response(context)

    def get_template_names(self):
        if self.not_found:
            return "reader/errors/_does_not_exist.html"
        return super(BaseReaderView, self).get_template_names()

    def render_to_response(self, context, **response_kwargs):
        if self.not_found:
            response_kwargs.setdefault('status', 404)
            context.update({
                'request': self.request,
                'page_title': _("%(object)s not found!") % {'object': context['not_found_object']},
                'title': _("Error 404")
            })
        return super(BaseReaderView, self).render_to_response(context, **response_kwargs)


class PublishedBookView(BaseReaderView, BasePageView, DetailView):
    # TODO: implement functionality when book is marked as published
    template_name = "reader/book_published.html"
    
    def render_to_response(self, context, **response_kwargs):
        try:
            book = self.get_object()
            if book:
                return redirect('reader:infopage', bookid=book.url_title)
        except:
            return super(PublishedBookView, self).render_to_response(context, **response_kwargs)


class InfoPageView(BaseReaderView, BasePageView, DetailView):
    template_name = "reader/book_info_page.html"
    page_title = _("Book Details Page")
    title = _("Book Details")

    def get_context_data(self, **kwargs):
        book = self.object
        book_version = book.get_version()
        book_security = security.getUserSecurityForBook(self.request.user, book)
        book_collaborators_ids = BookHistory.objects.filter(version = book_version, kind = 2).values_list('user', flat=True)
        
        context = super(InfoPageView, self).get_context_data(**kwargs)
        context['book_admins'] = book.bookipermission_set.filter(permission=1)
        context['book_collaborators'] = User.objects.filter(id__in=book_collaborators_ids)
        context['book_history'] = BookHistory.objects.filter(version = book_version).order_by('-modified')[:20]
        context['book_group'] = book.group
        context['is_book_admin'] = book_security.isAdmin()

        return context


class SingleNextMixin(object):
    """
    Just adds a next attribute to be used as redirect value
    after post action
    """

    def dispatch(self, request, *args, **kwargs):
        self.next = request.REQUEST.get('next', None)
        return super(SingleNextMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SingleNextMixin, self).get_context_data(**kwargs)
        context['next'] = self.next
        return context


class EditBookInfoView(SingleNextMixin, LoginRequiredMixin, BaseReaderView, UpdateView):
    template_name = "reader/book_info_edit.html"
    form_class = EditBookInfoForm
    context_object_name = 'book'

    def get_form(self, form_class):
        return form_class(user=self.request.user, **self.get_form_kwargs())

    def form_valid(self, form):
        self.object = form.save()

        if form.files.has_key('cover'):
            try:
                fh, fname = misc.save_uploaded_as_file(form.files['cover'])
                self.object.setCover(fname)
                os.unlink(fname)
            except:
                pass

        messages.success(self.request, _('Successfully changed book info.'))
        self.template_name = "reader/book_info_edit_redirect.html"
        return self.render_to_response(context=self.get_context_data())


class DeleteBookView(SingleNextMixin, LoginRequiredMixin, BaseReaderView, DeleteView):
    template_name = "reader/book_delete.html"

    def post(self, *args, **kwargs):
        request = self.request
        book = self.object = self.get_object()
        title = request.POST.get("title", "")
        book_security = security.getUserSecurityForBook(request.user, book)
        self.template_name = "reader/book_delete_error.html"

        try:
            if book_security.isAdmin() and title.strip() == book.title.strip():
                remove_book(book)
                self.template_name = "reader/book_delete_redirect.html"
                messages.success(request, _('Book successfully deleted.'))
        except Exception, e:
            raise e

        return self.render_to_response(context=self.get_context_data())


class DraftChapterView(BaseReaderView, BasePageView, DetailView):
    template_name = "reader/book_draft_page.html"
    page_title = _("Chapter Draft")
    title = ""

    def get_context_data(self, **kwargs):
        book = self.object
        book_version = book.get_version(self.kwargs.get('version', None))
        content = None

        # check permissions
        book_security = security.getUserSecurityForBook(self.request.user, book)
        has_permission = security.canEditBook(book, book_security)

        if book.hidden and not has_permission:
            return HttpResponseForbidden()

        if 'chapter' in self.kwargs:
            try:
                content = get_object_or_404(Chapter, version=book_version, url_title=self.kwargs['chapter'])
            except Http404:
                self.not_found = True
                context = dict(
                    not_found_object=_("Chapter"),
                    object_name=self.kwargs['chapter']
                )
                return context

        toc_items = BookToc.objects.filter(version=book_version).order_by("-weight")
        
        for chapter in toc_items:
            if not content and chapter.is_chapter():
                content = chapter.chapter
                break

        context = super(DraftChapterView, self).get_context_data(**kwargs)
        context['content'] = content
        context['toc_items'] = toc_items
        context['book_version'] = book_version.get_version()
        context['can_edit'] = (self.request.user.is_authenticated() and book.version == book_version)

        return context


class FullView(BaseReaderView, BasePageView, DetailView):
    template_name = "reader/book_full_view.html"
    page_title = _("Book full view")
    title = ""

    def get_context_data(self, **kwargs):
        book = self.object
        book_version = book.get_version(self.kwargs.get('version', None))
        toc_items = BookToc.objects.filter(version=book_version).order_by("-weight")

        context = super(FullView, self).get_context_data(**kwargs)
        context['book_version'] = book_version.get_version()
        context['toc_items'] = toc_items

        return context


class BookCoverView(BaseReaderView, DetailView):
    """
    Simple DetailView inherit clase to serve the book cover image
    """

    http_method_names = [u'get']
    
    def render_to_response(self, context, **response_kwargs):
        """
        Override render_to_response to serve the book cover static image
        """

        return static.serve(self.request, self.object.cover.name, settings.MEDIA_ROOT)