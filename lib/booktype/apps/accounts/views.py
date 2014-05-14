# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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
import datetime

from django.core.files import File
from django.shortcuts import render
from django.http import HttpResponse
from django.db import transaction, models
from django.views.generic import DetailView
from django.contrib.auth.models import User
from django.views.generic.edit import BaseCreateView
from django.utils.translation import ugettext_lazy as _

from booki.utils import config, misc
from booki.utils.json_wrapper import json
from booki.utils.book import checkBookAvailability, createBook
from booki.editor.models import Book, License, BookHistory, BookiGroup

from booktype.apps.core.views import BasePageView, PageView

class RegisterPageView(PageView):
    template_name = "accounts/register.html"
    page_title = _('Register')
    title = _('Please register')

    def get_context_data(self, **kwargs):
        context = super(RegisterPageView, self).get_context_data(**kwargs)

        return context

class DashboardPageView(BasePageView, DetailView):
    template_name = "accounts/dashboard.html"
    page_title = _('Dashboard')
    title = _('My Dashboard')

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['books'] = Book.objects.filter(owner=self.object)
        context['licenses'] = License.objects.all().order_by('name')
        context['groups'] = BookiGroup.objects.filter(owner=self.object)

        # get books with user has collaborated with
        book_ids = BookHistory.objects.filter(user=self.object).values_list('book', flat=True).distinct()
        context['books_collaborating'] = Book.objects.filter(id__in=book_ids).exclude(owner=self.object)

        # get user recent activity
        context['recent_activity'] = BookHistory.objects.filter(user=self.object).order_by('-modified')[:3]

        context['book_license'] = config.getConfiguration('CREATE_BOOK_LICENSE')
        context['book_visible'] = config.getConfiguration('CREATE_BOOK_VISIBLE')

        return context

class CreateBookView(BaseCreateView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'user'

    def get(self, request, *args, **kwargs):
        if request.GET.get('q', None) == "check":
            data = {
                "available": checkBookAvailability(request.GET.get('bookname', '').strip())
            }
            return HttpResponse(json.dumps(data), "application/json")

    def post(self, request, *args, **kwargs):
        book = createBook(request.user, request.POST.get('title'))
        lic = License.objects.get(abbrevation=request.POST.get('license'))

        book.license = lic
        book.description = request.POST.get('description', '')
        book.hidden = (request.POST.get('hidden', None) == 'on')

        if request.FILES.has_key('cover'):
            try:
                fh, fname = misc.saveUploadedAsFile(request.FILES['cover'])
                book.setCover(fname)
                os.unlink(fname)
            except:
                pass

        book.save()
    
        return render(
            request, 
            'accounts/create_book_redirect.html', 
            {"request": request, "book": book}
        )        