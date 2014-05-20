import datetime
import os

from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

from booktype.apps.core.views import PageView
from booktype.utils import misc
from booki.editor.models import Book, BookiGroup, BookHistory
from booki.account.models import UserProfile
from booki.utils.misc import bookiSlugify
from booki.utils import pages
from booktype.utils import security


class GroupManipulation(PageView):
    def post(self, request, groupid):
        group = BookiGroup.objects.get(url_name=groupid)
        if request.user.is_authenticated():
            if "task" not in request.POST:
                return pages.ErrorPage(request, "500.html")
            if(request.POST["task"] == "join-group"):
                group.members.add(request.user)
            else:
                group.members.remove(request.user)
        return HttpResponse()


class FrontPageView(PageView):
    template_name = "portal/frontpage.html"
    page_title = _('Booktype')
    title = _('Home')

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)

        context['books_list'] = Book.objects.filter(hidden=False).order_by('-created')[:4]
        context['user_list'] = User.objects.all().order_by('-date_joined')[:2]
        booki_group5 = BookiGroup.objects.all().order_by('-created')[:5]

        context['group_list'] = [{'url_name': g.url_name, 'name': g.name, 'description': g.description, 'num_members': g.members.count(), 'num_books': g.book_set.count(), 'small_group_image': g.get_group_image} for g in booki_group5]

        context['recent_activities'] = BookHistory.objects.filter(kind__in=[1, 10], book__hidden=False).order_by('-modified')[:5]

        return context


class GroupPageView(GroupManipulation):
    template_name = "portal/group.html"
    page_title = _('Group')
    title = _('Group used')

    def get_context_data(self, **kwargs):
        context = super(GroupPageView, self).get_context_data(**kwargs)
        selected_group = BookiGroup.objects.get(url_name=context['groupid'])

        context['user_group'] = {
            'url_name': selected_group.url_name, 'name': selected_group.name,
            'description': selected_group.description, 'num_members': selected_group.members.count(),
            'num_books': selected_group.book_set.count(), 'group_image': selected_group.get_big_group_image
        }

        context['group_members'] = selected_group.members.all()
        context['user_books'] = Book.objects.filter(group=selected_group, hidden=False)
        context['books_list'] = context['user_books'].order_by('-created')[:4]
        if self.request.user.is_authenticated():
            context['am_I_a_member'] = BookiGroup.objects.filter(members=self.request.user, url_name=context['groupid']).count()
        else:
            context['am_I_a_member'] = 0

        user_group_security = security.get_user_security_for_group(self.request.user, selected_group)

        if user_group_security.is_group_admin():
            context['show_group_settings'] = 1
        else:
            context['show_group_settings'] = 0

        return context


class AllGroupsPageView(GroupManipulation):
    template_name = "portal/all_groups.html"
    page_title = _('All groups')
    title = _('All groups')

    def get_context_data(self, **kwargs):
        context = super(AllGroupsPageView, self).get_context_data(**kwargs)

        book_group_sizes = Book.objects.filter(group__url_name__isnull=False).values('group__url_name').annotate(models.Count('id'))
        booki_groups_list = BookiGroup.objects.all()

        lista = []
        for i in booki_groups_list:
            num_books = 0
            book_count = filter(lambda x: x['group__url_name'] == i.url_name, book_group_sizes)
            if len(book_count) > 0:
                num_books = book_count[0]['id__count']
            lista.append({'url_name': i.url_name, 'name': i.name, 'description': i.description, 'members': i.members, 'num_books': num_books, 'small_group_image': i.get_group_image})
        context['all_groups'] = lista

        cut_off_date = datetime.datetime.today() - datetime.timedelta(days=30)
        book_history_activity = BookHistory.objects.filter(modified__gte=cut_off_date).filter(book__group__isnull=False)
        lista = []
        for i in book_history_activity:
            num_books = 0
            book_count = filter(lambda x: x['group__url_name'] == i.book.group.url_name, book_group_sizes)
            if len(book_count) > 0:
                num_books = book_count[0]['id__count']
            if len(filter(lambda x: x['url_name'] == i.book.group.url_name, lista)) == 0:
                lista.append({'url_name': i.book.group.url_name, 'name': i.book.group.name, 'description': i.book.group.description, 'members': i.book.group.members, 'num_books': num_books, 'small_group_image': i.book.group.get_group_image})
        context['active_groups'] = lista

        booki_group4 = BookiGroup.objects.all().order_by('-created')[:4]
        context['new_groups'] = [{'url_name': g.url_name, 'name': g.name, 'description': g.description, 'members': g.members, 'num_members': g.members.count(), 'num_books': g.book_set.count(), 'small_group_image': g.get_group_image} for g in booki_group4]

        return context


class GroupSettingsPageForm(forms.Form):
    name = forms.CharField()
    description = forms.CharField(required=False)


class GroupSettingsPageView(PageView):
    template_name = "portal/group_settings.html"
    form_class = GroupSettingsPageForm

    def post(self, request, groupid):
        form = self.form_class(request.POST)
        context = super(GroupSettingsPageView, self).get_context_data()
        new_desc = escape(form['description'].value())[:250]  # 250 characters

        if form.is_valid():
            if request.user.is_authenticated():
                new_name = form['name'].value()
                new_url_name = bookiSlugify(new_name)

                group = BookiGroup.objects.get(url_name=groupid)
                group_data_url_name = BookiGroup.objects.filter(url_name=new_url_name).exclude(pk=group.pk)

                if len(group_data_url_name) > 0:
                    context['error'] = {'name_error': _('Group name already used')}
                    context['selected_group'] = {'name': new_name, 'description': new_desc}
                    return render(request, self.template_name, context)

                if len(new_url_name) == 0:
                    context['error'] = {'name_error': _('Do not use special characters')}
                    context['selected_group'] = {'description': new_desc}
                    return render(request, self.template_name, context)

                try:
                    file_name = misc.set_group_image(str(group.pk), request.FILES['profile'], 240, 240)
                    if len(file_name) == 0:
                        context['error'] = {'image_error': _('Only JPEG file is allowed for group image.')}
                        context['selected_group'] = {'name': new_name, 'description': new_desc}
                        return render(request, self.template_name, context)
                    else:
                        misc.set_group_image(str(group.pk) + "_small", request.FILES['profile'], 18, 18)
                except:
                    pass

                group.url_name = new_url_name
                group.name = new_name
                group.description = new_desc
                group.save()
        else:
            context['error'] = {'name_error': _('Name should not be empty')}
            context['selected_group'] = {'description': new_desc}
            return render(request, self.template_name, context)

        return HttpResponseRedirect(reverse('portal:group', args=[new_url_name]))

    def get_context_data(self, **kwargs):
        context = super(GroupSettingsPageView, self).get_context_data(**kwargs)
        context['selected_group'] = BookiGroup.objects.get(url_name=kwargs['groupid'])

        return context


class PeoplePageView(PageView):
    template_name = "portal/people.html"
    page_title = _('People')
    title = _('People')

    def get_context_data(self, **kwargs):
        context = super(PeoplePageView, self).get_context_data(**kwargs)

        context['all_people'] = User.objects.all().extra(select={'lower_username': 'lower(username)'}).order_by('lower_username')

        now = datetime.datetime.now() - datetime.timedelta(30)
        context['active_people'] = [User.objects.get(id=b['user']) for b in BookHistory.objects.filter(modified__gte=now).values('user').annotate(models.Count('user')).order_by("-user__count")[:4]]

        context['new_people'] = User.objects.all().order_by('-date_joined')[:4]

        return context


class BooksPageView(PageView):
    template_name = "portal/books.html"
    page_title = _("Books")
    title = _("Books")

    def get_context_data(self, **kwargs):
        context = super(BooksPageView, self).get_context_data(**kwargs)

        context['books_list'] = Book.objects.filter(hidden=False).order_by('title')

        context['latest_books'] = Book.objects.filter(hidden=False).order_by('-created')[:2]

        context['published_books'] = Book.objects.filter(hidden=False, bookstatus=0).order_by('-created')[:2]

        context['latest_activity'] = BookHistory.objects.filter(kind__in=[1, 10], book__hidden=False).order_by('-modified')[:5]
        return context
