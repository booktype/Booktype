import datetime

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponse

from booktype.apps.core.views import PageView
from booki.editor.models import Book, BookiGroup, BookHistory
from booktype.apps.core.views import PageView
from django.views.generic import View, RedirectView


class FrontPageView(PageView):
    template_name = "portal/frontpage.html"
    page_title = _('Booktype')
    title = _('Home')

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)

        context['booksList'] = Book.objects.filter(hidden=False).order_by('-created')[:4]
        context['userList'] = User.objects.all().order_by('-date_joined')[:2]
        bookGroupSizes = Book.objects.filter(group__url_name__isnull=False).values('group__url_name').annotate(models.Count('id'))
        bookiGroupsList = BookiGroup.objects.values('url_name','name','description').annotate(models.Count('members'))
        lista = []
        for i in bookiGroupsList:
            num_books = 0
            book_count = filter(lambda x:x['group__url_name']==i['url_name'],bookGroupSizes)
            if len(book_count)>0:
                num_books = book_count[0]['id__count']
            lista.append({'url_name': i['url_name'],'name': i['name'], 'description': i['description'],'num_members': i['members__count'], 'num_books': num_books})
        context['groupList'] = lista
        context['bookList'] = BookiGroup.objects.annotate(num_books = models.Count('book__group'))
        context['booksInGroup'] = Book.objects.filter(hidden=False)

        context['recentActivities'] = BookHistory.objects.filter(kind__in=[1, 10], book__hidden=False).order_by('-modified')[:5]

        return context


class GroupPageView(PageView):
    template_name = "portal/group.html"
    page_title = _('Group')
    title = _('Group used')

    def post(self, request, groupid):
        group = BookiGroup.objects.get(url_name=groupid)
        if(request.user.is_authenticated()):
            if(request.POST["task"] == "join-group"):
                group.members.add(request.user)
            else:
                group.members.remove(request.user)
        return HttpResponse()

    def get_context_data(self, **kwargs):
        context = super(GroupPageView, self).get_context_data(**kwargs)

        bookGroupSizes = Book.objects.filter(group__url_name__isnull=False).values('group__url_name').annotate(models.Count('id'))
        bookiGroupElement = BookiGroup.objects.values('url_name','name','description').annotate(models.Count('members')).get(url_name=context['groupid'])
        num_books = 0
        book_count = filter(lambda x:x['group__url_name']==bookiGroupElement['url_name'],bookGroupSizes)
        if len(book_count)>0:
            num_books = book_count[0]['id__count']
        userGroup = {'url_name': bookiGroupElement['url_name'],'name': bookiGroupElement['name'], 'description': bookiGroupElement['description'],'num_members': bookiGroupElement['members__count'], 'num_books': num_books}
        context['userGroup'] = userGroup

        context['groupMembers'] = BookiGroup.objects.get(url_name=context['groupid']).members.all()
        context['userBooks'] = Book.objects.filter(group__url_name=userGroup['url_name'], hidden=False)
        context['booksList'] = context['userBooks'].order_by('-created')[:4]
        if(self.request.user.is_authenticated()):
            context['amIAMember'] = BookiGroup.objects.filter(members=self.request.user, url_name=context['groupid']).count()
        else:
            context['amIAMember'] = 0
        return context


class AllGroupsPageView(PageView):
    template_name = "portal/all_groups.html"
    page_title = _('All groups')
    title = _('All groups')

    def post(self, request, groupid):
        group = BookiGroup.objects.get(url_name=groupid)
        if(request.user.is_authenticated()):
            if(request.POST["task"] == "join-group"):
                group.members.add(request.user)
            else:
                group.members.remove(request.user)
        return HttpResponse()    

    def get_context_data(self, **kwargs):
        context = super(AllGroupsPageView, self).get_context_data(**kwargs)

        allGroups = BookiGroup.objects.annotate(num_members=models.Count('members'), num_books=models.Count('book'))
        context['allGroups'] = allGroups

        cutoffDate = datetime.datetime.today() - datetime.timedelta(days=30)
        bookGroupSizes = Book.objects.filter(group__url_name__isnull=False).values('group__url_name').annotate(models.Count('id'))
        bookHistoryActivity =  BookHistory.objects.filter(modified__gte=cutoffDate).filter(book__group__isnull=False) \
        .values('book__group__url_name', 'book__group__name', 'book__group__description', 'book__group__members').annotate(num_members=models.Count('book__group__members'))

        lista = []
        for i in bookHistoryActivity:
            num_books = 0
            book_count = filter(lambda x:x['group__url_name']==i['book__group__url_name'],bookGroupSizes)
            if len(book_count)>0:
                num_books = book_count[0]['id__count']
            lista.append({'url_name': i['book__group__url_name'],'name': i['book__group__name'], 'description': i['book__group__description'],'num_members': i['num_members'], 'num_books': num_books})        
        context['activeGroups'] = lista     
        context['newGroups'] = allGroups.order_by('-created')[:4]

        return context        