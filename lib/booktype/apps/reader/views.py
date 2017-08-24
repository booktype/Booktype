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
import logging
import json

from django.core.exceptions import PermissionDenied
from django.views import static
from django.http import Http404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, DeleteView, UpdateView

from braces.views import LoginRequiredMixin, JSONResponseMixin

from booktype.apps.core import views
from booktype.utils import misc, security
from booktype.utils.misc import get_available_themes
from booktype.utils.book import remove_book
from booktype.apps.core.views import BasePageView, NeverCacheMixin
from booktype.apps.themes.models import BookTheme
from booki.editor.models import Book, BookHistory, BookToc, Chapter

from .forms import EditBookInfoForm


logger = logging.getLogger('booktype')


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
                'page_title': _("%(object)s not found!") % {
                    'object': context['not_found_object']
                },
                'title': _("Error 404")
            })
        return super(BaseReaderView, self).render_to_response(
            context, **response_kwargs)


class PublishedBookView(BaseReaderView, BasePageView, DetailView):
    # TODO: implement functionality when book is marked as published
    template_name = "reader/book_published.html"

    def render_to_response(self, context, **response_kwargs):
        try:
            book = self.get_object()
            if book:
                return redirect('reader:infopage', bookid=book.url_title)
        except:
            return super(PublishedBookView, self).render_to_response(
                context, **response_kwargs)


class InfoPageView(views.SecurityMixin, BaseReaderView, BasePageView, DetailView):
    SECURITY_BRIDGE = security.BookSecurity
    template_name = "reader/book_info_page.html"
    page_title = _("Book Details Page")
    title = _("Book Details")

    def check_permissions(self, request, *args, **kwargs):
        can_view_book_info = self.security.has_perm("reader.can_view_book_info")
        can_view_hidden_book_info = self.security.has_perm("reader.can_view_hidden_book_info")

        if self.security.book.hidden and not can_view_hidden_book_info:
            raise PermissionDenied
        elif not can_view_book_info and not can_view_hidden_book_info:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        book = self.object
        book_version = book.get_version()

        book_collaborators_ids = BookHistory.objects.filter(
            version=book_version, kind=2).values_list('user', flat=True)

        context = super(InfoPageView, self).get_context_data(**kwargs)

        context['is_admin'] = self.request.user.is_superuser

        context['book_admins'] = book.bookipermission_set.filter(permission=1)
        context['book_collaborators'] = User.objects.filter(
            id__in=book_collaborators_ids)
        context['book_history'] = BookHistory.objects.filter(
            version=book_version).order_by('-modified')[:20]
        context['book_group'] = book.group
        context['is_book_admin'] = self.security.is_admin()

        return context


class PermissionsView(BaseReaderView, BasePageView, JSONResponseMixin, DetailView):
    """
    Returns the list of permissions a user has on one book
    """
    def render_to_response(self, context, **response_kwargs):
        book = self.object
        book_security = security.get_security_for_book(self.request.user, book)
        book_permissions = security.get_user_permissions(self.request.user, book)

        return self.render_json_response({
            'admin': book_security.is_admin(),
            'permissions': book_permissions,
        })


class SingleNextMixin(object):
    """
    Just adds a next attribute to be used as redirect value
    after post action
    """

    def dispatch(self, request, *args, **kwargs):
        _request_data = getattr(request, request.method)
        self.next = _request_data.get('next', None)
        return super(SingleNextMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SingleNextMixin, self).get_context_data(**kwargs)
        context['next'] = self.next
        return context


class EditBookInfoView(SingleNextMixin, LoginRequiredMixin,
                       BaseReaderView, UpdateView):
    template_name = "reader/book_info_edit.html"
    context_object_name = 'book'

    def get_form(self, form_class=EditBookInfoForm):
        return form_class(user=self.request.user, **self.get_form_kwargs())

    def form_valid(self, form):
        self.object = form.save()

        all_ok = True

        if 'book_cover' in form.files.keys():
            try:
                fh, fname = misc.save_uploaded_as_file(form.files['book_cover'])
                self.object.set_cover(fname)
                os.unlink(fname)
                self.object.save()
            except Exception, e:
                logger.exception(e)
                all_ok = False

        if all_ok:
            messages.success(self.request, _('Successfully changed book info.'))
        else:
            messages.warning(self.request, _('Could not upload cover image.'))

        self.template_name = "reader/book_info_edit_redirect.html"
        return self.render_to_response(context=self.get_context_data())


class DeleteBookView(SingleNextMixin, LoginRequiredMixin,
                     BaseReaderView, DeleteView):
    template_name = "reader/book_delete.html"

    def post(self, *args, **kwargs):
        request = self.request
        book = self.object = self.get_object()
        title = request.POST.get("title", "")
        book_security = security.get_security_for_book(request.user, book)
        book_permissions = security.get_user_permissions(request.user, book)
        self.template_name = "reader/book_delete_error.html"

        if (book_security.has_perm('edit.delete_book') and title.strip() == book.title.strip()):
            remove_book(book)
            self.template_name = "reader/book_delete_redirect.html"
            messages.success(request, _('Book successfully deleted.'))

        return self.render_to_response(context=self.get_context_data())


class DraftChapterView(views.SecurityMixin, BaseReaderView, BasePageView, DetailView):
    SECURITY_BRIDGE = security.BookSecurity
    template_name = "reader/book_draft_page.html"
    page_title = _("Chapter Draft")
    title = ""

    def check_permissions(self, request, *args, **kwargs):
        can_view_draft = self.security.has_perm("reader.can_view_draft")
        can_view_hidden_draft = self.security.has_perm("reader.can_view_hidden_draft")

        if self.security.book.hidden and not can_view_hidden_draft:
            raise PermissionDenied
        elif not can_view_draft and not can_view_hidden_draft:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        book = self.object
        content = None
        book_version = book.get_version(self.kwargs.get('version', None))
        context = super(DraftChapterView, self).get_context_data(**kwargs)

        if 'chapter' in self.kwargs:
            try:
                content = get_object_or_404(Chapter, version=book_version,
                                            url_title=self.kwargs['chapter'])
            except Http404:
                self.not_found = True
                context = dict(
                    not_found_object=_("Chapter"),
                    object_name=self.kwargs['chapter']
                )
                return context

        toc_items = BookToc.objects.filter(
            version=book_version).order_by("-weight")

        for chapter in toc_items:
            if not content and chapter.is_chapter():
                content = chapter.chapter
                break

        context['content'] = content
        context['toc_items'] = toc_items
        context['book_version'] = book_version.get_version()

        return context


class FullView(views.SecurityMixin, BaseReaderView, BasePageView, DetailView):
    SECURITY_BRIDGE = security.BookSecurity
    template_name = "reader/book_full_view.html"
    page_title = _("Book full view")
    title = ""

    def check_permissions(self, request, *args, **kwargs):
        can_view_full_page = self.security.has_perm("reader.can_view_full_page")
        can_view_hidden_full_page = self.security.has_perm("reader.can_view_hidden_full_page")

        if self.security.book.hidden and not can_view_hidden_full_page:
            raise PermissionDenied
        elif not can_view_full_page and not can_view_hidden_full_page:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        book = self.object
        context = super(FullView, self).get_context_data(**kwargs)

        book_version = book.get_version(self.kwargs.get('version', None))
        toc_items = BookToc.objects.filter(
            version=book_version).order_by("-weight")


        available_themes = get_available_themes()
        theme_active = available_themes[0]

        try:
            theme = BookTheme.objects.get(book=book)
            # override default one if it's available
            if theme.active in available_themes:
                theme_active = theme.active
            else:
                theme.active = theme_active
                theme.save()

        except BookTheme.DoesNotExist:
            theme = BookTheme(book=book, active=theme_active)
            theme.save()

        context['book_version'] = book_version.get_version()
        context['toc_items'] = toc_items
        context['theme'] = book.booktheme

        return context


class BookCoverView(NeverCacheMixin, BaseReaderView, DetailView):
    """
    Simple DetailView inherit clase to serve the book cover image
    """

    http_method_names = [u'get']

    def render_to_response(self, context, **response_kwargs):
        """
        Override render_to_response to serve the book cover static image
        """

        return static.serve(
            self.request, self.object.cover.name, settings.MEDIA_ROOT)
