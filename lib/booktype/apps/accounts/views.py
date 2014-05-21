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

from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import DetailView
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import BaseCreateView, UpdateView

from braces.views import LoginRequiredMixin

from booki.utils import config, misc
from booki.utils.json_wrapper import json
from booki.messaging.views import get_endpoint_or_none
from booki.utils.book import checkBookAvailability, createBook
from booki.editor.models import Book, License, BookHistory, BookiGroup

from booktype.apps.core.views import BasePageView, PageView

from .forms import UserSettingsForm, UserPasswordChangeForm

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

class CreateBookView(LoginRequiredMixin, BaseCreateView):
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

class UserSettingsPage(LoginRequiredMixin, BasePageView, UpdateView):
    template_name = "accounts/dashboard_settings.html"
    page_title = _('Settings')
    title = _('Settings')

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'current_user'
    form_class = UserSettingsForm
    password_form_class = UserPasswordChangeForm

    def dispatch(self, request, *args, **kwargs):
        dispatch_super = super(self.__class__, self).dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated():
            return dispatch_super

        if request.user.username == kwargs['username'] or request.user.is_superuser:
            return dispatch_super
        else:
            return redirect('accounts:user_settings', username=request.user.username)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['password_form'] = self.password_form_class(user=self.object)
        return context

    def form_valid(self, form):
        user = form.save()
        profile = user.get_profile()

        profile.description = form.data.get('aboutyourself', '')
        profile.save()

        if form.files.has_key('profile_pic'):
            try:
                misc.setProfileImage(user, form.files['profile_pic'])
            except:
                pass

        try:
            endpoint_config = get_endpoint_or_none("@"+user.username).get_config()
            endpoint_config.notification_filter = request.POST.get('notification', '')
            endpoint_config.save()
        except:
            pass

        # send a success message to user
        messages.success(self.request, _('User settings has been successfully saved!'))

        return redirect(self.get_success_url())

    def get_initial(self):
        initial = super(self.__class__, self).get_initial()
        initial['aboutyourself'] = self.object.get_profile().description
        endpoint = get_endpoint_or_none("@"+self.object.username)
        try:
            endpoint_config = endpoint.get_config()
            initial['notification'] = endpoint_config.notification_filter
        except Exception:
            initial['notification'] = ''

        return initial

    def get_success_url(self):
        return reverse('accounts:view_profile', args=[self.get_object().username])

    def post(self, request, *args, **kwargs):
        '''
        Overrides the post method in order to handle settings form and
        also password form
        '''
        
        if 'password_change' in request.POST:
            form = self.password_form_class(user=request.user, data=request.POST)
            if form.is_valid():
                # save password form
                form.save()

                # send a success message to user
                messages.success(self.request, _('Password changed successfully!'))

                return redirect(self.get_success_url())
            else:
                self.object = self.get_object()
                form_class = self.get_form_class()

                context = self.get_context_data()
                context.update({
                    'form': form_class(instance=self.object, initial=self.get_initial()),
                    'password_form': form,
                })

                return self.render_to_response(context)

        return super(self.__class__, self).post(request, *args, **kwargs)
