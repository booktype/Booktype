import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.views.generic.edit import CreateView, UpdateView

from braces.views import LoginRequiredMixin

from booktype.apps.core import views
from booktype.utils import security
from booktype.utils.misc import booktype_slugify
from booktype.apps.core.views import PageView, BasePageView
from booki.editor.models import Book, BookiGroup, BookHistory

from .forms import GroupCreateForm, GroupUpdateForm


class GroupManipulation(PageView):
    def post(self, request, groupid):
        group = BookiGroup.objects.get(url_name=groupid)
        if request.user.is_authenticated():
            if "task" not in request.POST:
                return views.ErrorPage(request, "errors/500.html")
            if request.POST["task"] == "join-group":
                group.members.add(request.user)
            if request.POST["task"] == "leave-group":
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

    def render_to_response(self, context, **response_kwargs):
        if context['selected_group_error']:
            return views.ErrorPage(self.request, "portal/errors/group_does_not_exist.html", {"group_name": context['groupid']})

        return super(self.__class__, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupPageView, self).get_context_data(**kwargs)
        try:
            context['selected_group'] = BookiGroup.objects.get(url_name=context['groupid'])
        except BookiGroup.DoesNotExist:
            context['selected_group_error'] = True
            return context
        except BookiGroup.MultipleObjectsReturned:
            context['selected_group_error'] = True
            return context
        context['selected_group_error'] = False

        context['user_group'] = {
            'url_name': context['selected_group'].url_name, 'name': context['selected_group'].name,
            'description': context['selected_group'].description, 'num_members': context['selected_group'].members.count(),
            'num_books': context['selected_group'].book_set.count(), 'group_image': context['selected_group'].get_big_group_image
        }

        context['group_members'] = context['selected_group'].members.all()
        context['user_books'] = Book.objects.filter(group=context['selected_group'], hidden=False)
        context['books_list'] = context['user_books'].order_by('-created')

        context['books_to_add'] = []

        user_group_security = security.get_user_security_for_group(self.request.user, context['selected_group'])
        context['is_group_admin'] = user_group_security.is_group_admin()

        if context['is_group_admin']:
            list_of_books = Book.objects.exclude(group=context['selected_group'])

            for b in list_of_books:
                if security.get_user_security_for_book(self.request.user, b).is_book_admin():
                    context['books_to_add'].append({'cover': b.cover, 'url_title': b.url_title, 'title': b.title})

            if self.request.user.is_superuser:
                context['books_to_add'] = list_of_books

            context['am_I_a_member'] = BookiGroup.objects.filter(members=self.request.user, url_name=context['groupid']).count()
        else:
            context['am_I_a_member'] = 0

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
            lista.append({'url_name': i.url_name, 'name': i.name, 'description': i.description, 'owner': i.owner, 'members': i.members, 'num_books': num_books, 'small_group_image': i.get_group_image})
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
        context['new_groups'] = [{'url_name': g.url_name, 'name': g.name, 'description': g.description, 'members': g.members, 'owner': g.owner, 'num_members': g.members.count(), 'num_books': g.book_set.count(), 'small_group_image': g.get_group_image} for g in booki_group4]

        return context


class GroupCreateView(LoginRequiredMixin, BasePageView, CreateView):
    template_name = "portal/group_create.html"
    model = BookiGroup
    slug_field = 'url_name'
    form_class = GroupCreateForm
    slug_url_kwarg = 'groupid'
    page_title = _('Create new group')

    def dispatch(self, request, *args, **kwargs):
        """
        Checks if request is an ajax call and change template_name
        to a modal window
        """

        if request.is_ajax():
            self.template_name = "portal/group_create_modal.html"

        return super(GroupCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        group = form.save(commit=False)
        group.owner = self.request.user
        group.url_name = booktype_slugify(group.name)
        group.created = timezone.now()
        group.save()

        # auto-join owner as team member
        group.members.add(self.request.user)

        # set group image if exists in post data
        group_image = form.files.get('group_image', None)
        if group_image:
            form.set_group_image(group.pk, group_image)

        return super(GroupCreateView, self).form_valid(form)


class GroupUpdateView(LoginRequiredMixin, BasePageView, UpdateView):
    template_name = "portal/group_settings.html"
    model = BookiGroup
    slug_field = 'url_name'
    slug_url_kwarg = 'groupid'
    form_class = GroupUpdateForm
    page_title = _('Group settings')

    def dispatch(self, request, *args, **kwargs):
        """
        Checks if user is a group admin. If not, return no permissions page
        """

        self.object = self.get_object()
        group_security = security.get_user_security_for_group(request.user, self.object)

        if not group_security.is_group_admin():
            return views.ErrorPage(request, "errors/nopermissions.html")

        return super(GroupUpdateView, self).dispatch(request, *args, **kwargs)


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


class AddBooksView(PageView):
    template_name = "portal/portal_add_book_modal.html"

    def post(self, request, groupid):
        if request.user.is_authenticated():
            if "task" not in request.POST:
                return views.ErrorPage(request, "errors/500.html")

            if request.POST["task"] == "add-book":
                group = BookiGroup.objects.get(url_name=groupid)
                books_list = request.POST["books"].split(',')
                for i in books_list:
                    book = Book.objects.get(url_title=i)
                    book.group = group
                    book.save()

        return HttpResponse()        