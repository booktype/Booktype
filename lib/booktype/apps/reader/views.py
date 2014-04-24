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

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.views.generic import DetailView, DeleteView, UpdateView
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

from braces.views import LoginRequiredMixin

from booki.utils import misc, security
from booki.utils.book import removeBook
from booki.editor.models import Book, BookHistory, BookToc, Chapter
from booktype.apps.core.views import BasePageView

class BaseReaderView(object):
    """
    Base Reader View Class with the common attributes
    """

    model = Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    context_object_name = 'book'

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

class EditBookInfoView(LoginRequiredMixin, BaseReaderView, UpdateView):
    template_name = "reader/book_info_edit.html"

    def post(self, *args, **kwargs):
        request = self.request
        book = self.object = self.get_object()
        book.description = request.POST.get('description', '')

        if request.FILES.has_key('cover'):
            try:
                fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                book.setCover(fname)
                os.unlink(fname)
            except:
                pass

        try:
            book.save()
            self.template_name = "reader/book_info_edit_redirect.html"
        except Exception, e:
            raise e

        return self.render_to_response({
            'book': book
        })

class DeleteBookView(LoginRequiredMixin, BaseReaderView, DeleteView):
    template_name = "reader/book_delete.html"

    def post(self, *args, **kwargs):
        request = self.request
        book = self.object = self.get_object()
        title = request.POST.get("title", "")
        book_security = security.getUserSecurityForBook(request.user, book)
        self.template_name = "reader/book_delete_error.html"

        try:
            if book_security.isAdmin() and title.strip() == book.title.strip():
                removeBook(book)
                self.template_name = "reader/book_delete_redirect.html"
        except Exception, e:
            raise e

        return self.render_to_response({
            'request': request
        })

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
            content = get_object_or_404(Chapter, version=book_version, url_title=self.kwargs['chapter'])

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