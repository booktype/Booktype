import datetime
import logging

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.generic import DeleteView
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView

from braces.views import LoginRequiredMixin

from booktype.apps.core import views
from booktype.utils import security, config
from booktype.utils.misc import booktype_slugify, has_book_limit
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


class FrontPageView(views.SecurityMixin, PageView):
    template_name = "portal/frontpage.html"
    page_title = _('Booktype')
    title = _('Home')

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)

        if config.get_configuration('BOOKTYPE_FRONTPAGE_USE_ANONYMOUS_PAGE') and self.request.user.is_anonymous():
            self.template_name = "portal/anonymous_frontpage.html"
            context['anonymous_message'] = config.get_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_MESSAGE')
            context['anonymous_email'] = config.get_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_EMAIL')
            context['anonymous_image'] = config.get_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_IMAGE')
            return context

        context['is_admin'] = self.request.user.is_superuser
        # get all user permissions
        role_key = security.get_default_role_key(self.request.user)
        default_role = security.get_default_role(role_key)
        if default_role:
            context['roles_permissions'] = [p.key_name for p in default_role.permissions.all()]
        else:
            context['roles_permissions'] = []

        b_query = Book.objects.all()

        if not self.request.user.is_superuser:
            if self.request.user.is_authenticated():
                b_query = b_query.filter(Q(hidden=False) | Q(owner=self.request.user))
            else:
                b_query = b_query.filter(hidden=False)

        context['books_list'] = b_query.order_by('-created')[:10]
        context['user_list'] = User.objects.filter(is_active=True).order_by('-date_joined')[:12]
        booki_group5 = BookiGroup.objects.all().order_by('-created')[:6]

        context['group_list'] = [{
            'url_name': g.url_name,
            'name': g.name,
            'description': g.description,
            'num_members': g.members.count(),
            'num_books': g.book_set.count(),
            'small_group_image': g.get_group_image
            } for g in booki_group5]

        context['recent_activities'] = BookHistory.objects.filter(kind__in=[1, 10], book__hidden=False).order_by('-modified')[:5]

        context['is_book_limit'] = has_book_limit(self.request.user)

        if self.request.user.is_superuser:
            context['can_create_book'] = True
            context['is_book_limit'] = False
        # if only admin create then deny user permission to create new books
        elif config.get_configuration('ADMIN_CREATE_BOOKS'):
            context['can_create_book'] = False
        # check if user can create more books
        elif context['is_book_limit']:
            context['can_create_book'] = False
        else:
            context['can_create_book'] = True

        return context


class GroupPageView(views.SecurityMixin, GroupManipulation):
    SECURITY_BRIDGE = security.GroupSecurity
    template_name = "portal/group.html"
    page_title = _('Group')

    def check_permissions(self, request, *args, **kwargs):
        if not self.security.has_perm("portal.can_view_group_info"):
            raise PermissionDenied

    def render_to_response(self, context, **response_kwargs):
        if context['selected_group_error']:
            return views.ErrorPage(self.request, "portal/errors/group_does_not_exist.html", {"group_name": context['groupid']})

        return super(GroupPageView, self).render_to_response(context, **response_kwargs)

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
        context['title'] = context['selected_group'].name

        context['group_members'] = context['selected_group'].members.all()
        if self.request.user.is_superuser:
            context['books_list'] = Book.objects.filter(group=context['selected_group']).order_by('-created')
        else:
            context['books_list'] = Book.objects.filter(
                Q(group=context['selected_group']), Q(hidden=False) | Q(owner=self.request.user)
            ).order_by('-created')

        context['user_group'] = {
            'url_name': context['selected_group'].url_name, 'name': context['selected_group'].name,
            'description': context['selected_group'].description, 'num_members': context['selected_group'].members.count(),
            'num_books': context['books_list'].count(), 'group_image': context['selected_group'].get_big_group_image
        }

        context['books_to_add'] = []

        user_group_security = security.get_security_for_group(self.request.user, context['selected_group'])
        context['is_group_admin'] = user_group_security.is_group_admin()

        if context['is_group_admin']:
            if self.request.user.is_superuser:
                # Last filter (group__isnull=True) should be removed when Book model will support multiple groups
                list_of_books = Book.objects.exclude(group=context['selected_group']).\
                    filter(group__isnull=True)
            else:
                # Last filter (group__isnull=True) should be removed when Book model will support multiple groups
                list_of_books = Book.objects.exclude(group=context['selected_group']).\
                    filter(owner=self.request.user).\
                    filter(group__isnull=True)

            for b in list_of_books:
                context['books_to_add'].append({'id': b.id, 'cover': b.cover, 'url_title': b.url_title, 'title': b.title})

        context['is_group_member'] = self.request.user in context['group_members']

        return context


class AllGroupsPageView(views.SecurityMixin, GroupManipulation):
    template_name = "portal/all_groups.html"
    page_title = _('Groups')
    title = _('Groups')

    def check_permissions(self, request, *args, **kwargs):
        if not self.security.has_perm("portal.can_view_groups_list"):
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(AllGroupsPageView, self).get_context_data(**kwargs)

        book_group_sizes = Book.objects.filter(group__url_name__isnull=False).\
            filter(Q(hidden=False) | Q(owner=self.request.user)).\
            values('group__url_name').\
            annotate(models.Count('id'))

        paginator = Paginator(BookiGroup.objects.all(), config.get_configuration('GROUP_LIST_PAGE_SIZE'))

        try:
            booki_groups_list_page = paginator.page(self.request.GET.get('page'))
        except PageNotAnInteger:
            booki_groups_list_page = paginator.page(1)
        except EmptyPage:
            booki_groups_list_page = paginator.page(paginator.num_pages)

        lista = []
        for i in booki_groups_list_page:
            num_books = 0
            book_count = filter(lambda x: x['group__url_name'] == i.url_name, book_group_sizes)
            if len(book_count) > 0:
                num_books = book_count[0]['id__count']
            lista.append({'url_name': i.url_name,
                          'name': i.name,
                          'description': i.description,
                          'owner': i.owner,
                          'members': i.members,
                          'num_books': num_books,
                          'small_group_image': i.get_group_image})

        context['all_groups'] = lista
        context['all_groups_page'] = booki_groups_list_page

        cut_off_date = datetime.datetime.today() - datetime.timedelta(days=30)
        book_history_activity = BookHistory.objects.filter(modified__gte=cut_off_date).filter(book__group__isnull=False)
        lista = []
        for i in book_history_activity:
            num_books = 0
            book_count = filter(lambda x: x['group__url_name'] == i.book.group.url_name, book_group_sizes)
            if len(book_count) > 0:
                num_books = book_count[0]['id__count']
            if len(filter(lambda x: x['url_name'] == i.book.group.url_name, lista)) == 0:
                lista.append({'url_name': i.book.group.url_name,
                              'name': i.book.group.name,
                              'description': i.book.group.description,
                              'members': i.book.group.members,
                              'num_books': num_books,
                              'small_group_image': i.book.group.get_group_image})

        context['active_groups'] = lista

        booki_group4 = BookiGroup.objects.all().order_by('-created')[:4]
        context['new_groups'] = [{'url_name': g.url_name,
                                  'name': g.name,
                                  'description': g.description,
                                  'members': g.members,
                                  'owner': g.owner,
                                  'num_members': g.members.count(),
                                  'num_books': g.book_set.count(),
                                  'small_group_image': g.get_group_image} for g in booki_group4]

        return context


class GroupCreateView(LoginRequiredMixin, BasePageView, CreateView):
    template_name = "portal/group_create.html"
    model = BookiGroup
    slug_field = 'url_name'
    form_class = GroupCreateForm
    slug_url_kwarg = 'groupid'
    page_title = _('Create New Group')

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
        group_security = security.get_security_for_group(request.user, self.object)

        if not group_security.is_admin():
            return views.ErrorPage(request, "errors/nopermissions.html")

        return super(GroupUpdateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial_dict = super(GroupUpdateView, self).get_initial()
        group = self.get_object()
        group_image = group.get_big_group_image()

        if group_image:
            initial_dict['group_image'] = group_image
        return initial_dict

    def form_valid(self, form):
        response = super(GroupUpdateView, self).form_valid(form)
        if form.data.get('group_image_remove', False) and not form.files.get('group_image'):
            form.instance.remove_group_images()
        return response


class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = BookiGroup
    slug_field = 'url_name'
    slug_url_kwarg = 'groupid'
    context_object_name = 'group'
    template_name = 'portal/group_delete_modal.html'

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        group = self.get_object()
        group_security = security.get_security_for_group(user, group)

        if group.owner != user and not user.is_superuser or not group_security.is_group_admin():
            messages.warning(self.request, _("You are not allowed to delete this group"))
            return HttpResponseRedirect(self.get_success_url())
        else:
            # remove books from group
            group.book_set.update(group=None)

            # delete group images if needed
            try:
                group.remove_group_images()
            except Exception as e:
                print e

            messages.success(self.request, _('Group successfully deleted.'))
        return super(GroupDeleteView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('accounts:view_profile', args=[self.request.user.username])


class PeoplePageView(views.SecurityMixin, PageView):
    template_name = "portal/people.html"
    page_title = _('People')
    title = _('People')

    def check_permissions(self, request, *args, **kwargs):
        if not self.security.has_perm("portal.can_view_user_list"):
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(PeoplePageView, self).get_context_data(**kwargs)

        user_list_qs = User.objects.filter(is_active=True).extra(
            select={'lower_username': 'lower(username)'}).order_by('lower_username')

        paginator = Paginator(user_list_qs, config.get_configuration('USER_LIST_PAGE_SIZE'))

        try:
            context['all_people'] = paginator.page(self.request.GET.get('page'))
        except PageNotAnInteger:
            context['all_people'] = paginator.page(1)
        except EmptyPage:
            context['all_people'] = paginator.page(paginator.num_pages)

        now = datetime.datetime.now() - datetime.timedelta(30)
        context['active_people'] = [User.objects.get(id=b['user']) for b in BookHistory.objects.filter(modified__gte=now, user__is_active=True).values('user').annotate(models.Count('user')).order_by("-user__count")[:4]]

        context['new_people'] = User.objects.filter(is_active=True).order_by('-date_joined')[:4]

        return context


class BooksPageView(views.SecurityMixin, PageView):
    template_name = "portal/books.html"
    page_title = _("Books")
    title = _("Books")

    def check_permissions(self, request, *args, **kwargs):
        if not self.security.has_perm("portal.can_view_books_list"):
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(BooksPageView, self).get_context_data(**kwargs)

        b_query = Book.objects.all()
        if not self.request.user.is_superuser:
            if self.request.user.is_authenticated():
                b_query = b_query.filter(Q(hidden=False) | Q(owner=self.request.user))
            else:
                b_query = b_query.filter(hidden=False)

        paginator = Paginator(b_query.order_by('title'), config.get_configuration('BOOK_LIST_PAGE_SIZE'))

        try:
            context['books_list'] = paginator.page(self.request.GET.get('page'))
        except PageNotAnInteger:
            context['books_list'] = paginator.page(1)
        except EmptyPage:
            context['books_list'] = paginator.page(paginator.num_pages)

        context['latest_books'] = b_query.order_by('-created')[:2]

        context['published_books'] = b_query.filter(bookstatus=0).order_by('-created')[:2]

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


class RemoveBookView(LoginRequiredMixin, PageView):
    template_name = "portal/group_remove_book.html"

    def get_context_data(self, **kwargs):
        context = super(RemoveBookView, self).get_context_data(**kwargs)
        context['book'] = Book.objects.get(url_title=context['bookid'])
        context['group'] = BookiGroup.objects.get(url_name=context['groupid'])
        return context

    def post(self, request, groupid, bookid):
        logger = logging.getLogger('booktype')
        try:
            if request.user.is_authenticated():
                book_url = bookid
                book = Book.objects.get(url_title=book_url)
                book.group = None
                book.save()

            return HttpResponseRedirect(reverse('portal:group', args=[groupid]))
        except IOError as e:
            logger.exception(e)
            return HttpResponse(status=500)
