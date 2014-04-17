import datetime

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import transaction, models

from booki.editor.models import Book, BookiGroup, BookHistory
from booktype.apps.core.views import PageView
from django.views.generic import View, RedirectView


class RegisterPageView(PageView):
    template_name = "accounts/register.html"
    page_title = _('Register')
    title = _('Please register')

    def get_context_data(self, **kwargs):
        context = super(RegisterPageView, self).get_context_data(**kwargs)

        return context


class GroupPageView(PageView):
    template_name = "accounts/group.html"
    page_title = _('Group')
    title = _('Group used')

    def post(self, request, groupid):
        group = BookiGroup.objects.get(url_name=groupid)
        if(request.POST["task"] == "join-group"):
            group.members.add(request.user)
        else:
            group.members.remove(request.user)
        transaction.commit()
        return HttpResponse()

    def get_context_data(self, **kwargs):
        context = super(GroupPageView, self).get_context_data(**kwargs)

        userGroup = BookiGroup.objects.filter(url_name=context['groupid']).annotate(num_members=models.Count('members'), num_books=models.Count('book'))
        context['userGroup'] = userGroup
        context['userBooks'] = Book.objects.filter(group=userGroup, hidden=False)
        context['booksList'] = context['userBooks'].order_by('-created')[:4]
        if(self.request.user.is_authenticated()):
            context['amIAMember'] = BookiGroup.objects.filter(members=self.request.user, url_name=context['groupid']).count()
        else:
            context['amIAMember'] = 0
        return context


class AllGroupsPageView(PageView):
    template_name = "accounts/all_groups.html"
    page_title = _('All groups')
    title = _('All groups')

    def get_context_data(self, **kwargs):
        context = super(AllGroupsPageView, self).get_context_data(**kwargs)

        allGroups = BookiGroup.objects.annotate(num_members=models.Count('members'), num_books=models.Count('book'))
        context['allGroups'] = allGroups

        cutoffDate = datetime.datetime.today() - datetime.timedelta(days=30)
        context['activeGroups'] = BookHistory.objects.filter(modified__gte=cutoffDate).filter(book__group__isnull=False)  \
            .values('book__group__url_name', 'book__group__name', 'book__group__description', 'book__group__members') \
            .annotate(num_members=models.Count('book__group__members'), num_books=models.Count('book'))
        context['newGroups'] = allGroups.order_by('-created')[:4]

        return context
