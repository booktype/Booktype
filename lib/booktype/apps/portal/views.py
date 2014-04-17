from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db import models

from booktype.apps.core.views import PageView
from booki.editor.models import Book, BookiGroup, BookHistory


class FrontPageView(PageView):
    template_name = "portal/frontpage.html"
    page_title = _('Booktype')
    title = _('Home')

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)

        context['booksList'] = Book.objects.filter(hidden=False).order_by('-created')[:4]
        context['userList'] = User.objects.all().order_by('-date_joined')[:2]
        context['groupList'] = BookiGroup.objects.annotate(num_members=models.Count('members'), num_books=models.Count('book'))
        context['booksInGroup'] = Book.objects.filter(hidden=False)

        context['recentActivities'] = BookHistory.objects.filter(kind__in=[1, 10], book__hidden=False).order_by('-modified')[:5]

        return context