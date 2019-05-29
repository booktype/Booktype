# -*- coding: utf-8 -*-
import re
import os
import json
import uuid
import hashlib
import logging
import zipfile
import difflib
import StringIO
import datetime
import operator
import mimetypes
import unidecode

from lxml.html.diff import htmldiff

from django.utils import formats
from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, FormView
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden

from braces.views import (LoginRequiredMixin, JSONResponseMixin)
from compressor.base import Compressor

from booki.editor import models
from booki.utils.log import logChapterHistory, logBookHistory

from booktype.apps.core import views
from booktype.apps.core.models import BookRole
from booktype.utils import security, config
from booktype.utils.misc import booktype_slugify
from booktype.apps.convert.plugin import TocSettings
from booktype.apps.reader.views import BaseReaderView
from booktype.convert import loader as convert_loader
from booktype.apps.convert import utils as convert_utils
from booktype.apps.importer.forms import UploadDocxFileForm
from booktype.utils.security import BookSecurity, get_user_permissions

from .utils import color_me, send_notification, clean_chapter_html
from .channel import get_toc_for_book
from . import forms as book_forms

logger = logging.getLogger('booktype.apps.edit.views')


VALID_SETTINGS = {
    'general': _('General Settings'),
    'language': _('Book Language'),
    'license': _('Book License'),
    'metadata': _('Book Metadata'),
    'additional-metadata': _('Additional Metadata'),
    'roles': _('Roles'),
    'permissions': _('Permissions'),
    'chapter-status': _('Chapter Status'),
}

getTOCForBook = get_toc_for_book


@login_required
@transaction.atomic
def upload_attachment(request, bookid, version=None):
    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(
            request, "errors/book_does_not_exist.html", {"book_name": bookid})

    user = request.user
    book_security = security.get_security_for_book(user, book)
    can_upload_attachment = book_security.has_perm('edit.upload_attachment')

    if (not user.is_superuser and not can_upload_attachment and book.owner != user):
        raise PermissionDenied

    book_version = book.get_version(version)
    stat = models.BookStatus.objects.filter(book=book)[0]

    with transaction.atomic():
        file_data = request.FILES['files[]']
        att = models.Attachment(
            version=book_version,
            # must remove this reference
            created=datetime.datetime.now(),
            book=book,
            status=stat
        )
        att.save()

        attName, attExt = os.path.splitext(file_data.name)
        att.attachment.save(
            '{}{}'.format(booktype_slugify(attName), attExt),
            file_data,
            save=False
        )
        att.save()

    response_data = {}

    # add cliendID and sputnikID to request object
    # this will allow us to use sputnik and addMessageToChannel
    request.clientID = request.POST['clientID']
    request.sputnikID = "%s:%s" % (request.session.session_key, request.clientID)
    send_notification(request, book.id, book_version.get_version(),
                      "notification_new_attachment_uploaded", att.get_name())

    if "application/json" in request.META['HTTP_ACCEPT']:
        return HttpResponse(json.dumps(response_data),
                            content_type="application/json")
    else:
        return HttpResponse(json.dumps(response_data), content_type="text/html")


@login_required
@transaction.atomic
def upload_cover(request, bookid, version=None):
    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html",
                               {"book_name": bookid})

    can_upload_cover = security.get_security_for_book(request.user, book).has_perm('edit.upload_cover')

    if (not request.user.is_superuser and not can_upload_cover and book.owner != request.user):
        raise PermissionDenied

    with transaction.atomic():
        file_data = request.FILES['files[]']
        title = request.POST.get('title', '')
        try:
            filename = unidecode.unidecode(file_data.name)
        except:
            filename = uuid.uuid1().hex

        h = hashlib.sha1()
        h.update(filename)
        h.update(unidecode.unidecode(title))
        h.update(str(datetime.datetime.now()))

        license = models.License.objects.get(
            abbrevation=request.POST.get('license', ''))

        cover = models.BookCover(
            book=book,
            user=request.user,
            cid=h.hexdigest(),
            title=title,
            filename=filename[:250],
            width=0,
            height=0,
            unit=request.POST.get('unit', 'mm'),
            booksize=request.POST.get('booksize', ''),
            cover_type=request.POST.get('type', ''),
            creator=request.POST.get('creator', '')[:40],
            license=license,
            notes=request.POST.get('notes', '')[:500],
            approved=False,
            is_book=False,
            is_ebook=True,
            is_pdf=False,
            created=datetime.datetime.now()
        )
        cover.save()

        # now save the attachment
        cover.attachment.save(filename, file_data, save=False)
        cover.save()

    response_data = {
        "files": [{
            "url": "http://127.0.0.1/",
            "thumbnail_url": "http://127.0.0.1/",
            "name": "boot.png",
            "type": "image/png",
            "size": 172728,
            "delete_url": "",
            "delete_type": "DELETE"
        }]
    }

    # add cliendID and sputnikID to request object
    # this will allow us to use sputnik and addMessageToChannel
    request.clientID = request.POST['clientID']
    request.sputnikID = "%s:%s" % (request.session.session_key, request.clientID)
    send_notification(request, book.id, book.get_version(version).get_version(),
                      "notification_new_cover_uploaded", cover.title)

    if "application/json" in request.META['HTTP_ACCEPT']:
        return HttpResponse(json.dumps(response_data),
                            content_type="application/json")
    else:
        return HttpResponse(json.dumps(response_data), content_type="text/html")


def unified_diff(content1, content2):
    try:
        content1 = clean_chapter_html(content1, clean_comments_trail=True)
        content2 = clean_chapter_html(content2, clean_comments_trail=True)
    except Exception as e:
        logger.error('ERROR while cleaning content %s. Rev 1: %s Chapter: %s' % (
            e, content1, content2))
        return {"result": False}

    diff = htmldiff(content1, content2)
    return diff


def split_diff(content1, content2):
    """
    Method that receives to html strings as parameters and a diff is
    returned as HTML string and is used for parallel comparison.
    """

    output = []
    output_left = '<td valign="top">'
    output_right = '<td valign="top">'

    def _fix_content(cnt):
        list_of_tags = ['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        for _t in list_of_tags:
            cnt = cnt.replace('<{}>'.format(_t), '\n<{}>'.format(_t))
            if _t != 'p':
                cnt = cnt.replace('</{}>'.format(_t), '</{}>\n'.format(_t))

        cnt = cnt.replace('\n\n', '\n')
        cnt = cnt.replace('. ', '. \n')

        return cnt

    content1 = re.sub('<[^<]+?>', '', _fix_content(content1)).splitlines()
    content1 = [x.lstrip() for x in content1]

    content2 = re.sub('<[^<]+?>', '', _fix_content(content2)).splitlines()
    content2 = [x.lstrip() for x in content2]

    lns = [line for line in difflib.ndiff(content1, content2)]

    n = 0
    minus_pos = None
    plus_pos = None

    def my_find(s, wh, x=0):
        n = x
        for ch in s[n:]:
            if ch in wh:
                return n
            n += 1
        return -1

    while True:
        if n >= len(lns):
            break

        line = lns[n]

        if line[:2] == '+ ':
            if n + 1 < len(lns) and lns[n + 1][0] == '?':
                lns[n + 1] += lns[n + 1] + ' '
                x = my_find(lns[n + 1][2:], '+?^-')
                y = lns[n + 1][2:].find(' ', x) - 2
                plus_pos = (x, y)
            else:
                plus_pos = None

            output_right += '<div class="diff changed">%s</div>' % \
                color_me(line[2:], 'diff added', plus_pos)
            output.append(
                '<tr>%s</td>%s</td></tr>' % (output_left, output_right))
            output_left = output_right = '<td valign="top">'

        elif line[:2] == '- ':
            if n + 1 < len(lns) and lns[n + 1][0] == '?':
                lns[n + 1] += lns[n + 1] + ' '
                x = my_find(lns[n + 1][2:], '+?^-')
                y = lns[n + 1][2:].find(' ', x) - 2
                minus_pos = (x, y)
            else:
                minus_pos = None

            output.append(
                '<tr>%s</td>%s</td></tr>' % (output_left, output_right))

            output_left = output_right = '<td valign="top">'
            output_left += '<div class="diff changed">%s</div>' % color_me(
                line[2:], 'diff deleted', minus_pos)

        elif line[:2] == '  ':
            if line[2:].strip() != '':
                output_left += line[2:] + '<br/><br/>'
                output_right += line[2:] + '<br/><br/>'

        n += 1

    output.append('<tr>%s</td>%s</td></tr>' % (output_left, output_right))
    output = '<table border="0" width="100%" class="row compare_table">' + "".join(output) + '</table>'

    return mark_safe(output)


def cover(request, bookid, cid, fname=None, version=None):

    try:
        models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(
            request, "errors/book_does_not_exist.html", {"book_name": bookid})

    try:
        cover = models.BookCover.objects.get(cid=cid)
    except models.BookCover.DoesNotExist:
        return HttpResponse(status=500)

    document_path = cover.attachment.path

    # extenstion
    mimetypes.init()
    extension = cover.attachment.name.split('.')[-1].lower()

    if extension == 'tif':
        extension = 'tiff'

    if extension == 'jpg':
        extension = 'jpeg'

    content_type = mimetypes.types_map.get(
        '.' + extension, 'binary/octet-stream')

    if request.GET.get('preview', '') == '1':
        try:
            from PIL import Image
        except ImportError:
            import Image

        try:
            if extension.lower() in ['pdf', 'psd', 'svg']:
                raise Exception

            im = Image.open(cover.attachment.name)
            im.thumbnail((300, 200), Image.ANTIALIAS)
        except:
            try:
                im = Image.open('%s/edit/img/booktype-cover-%s.png' %
                                (settings.STATIC_ROOT, extension.lower()))
                extension = 'png'
                content_type = 'image/png'
            except:
                # Not just IOError but anything else
                im = Image.open('%s/edit/img/booktype-cover-error.png' %
                                settings.STATIC_ROOT)
                extension = 'png'
                content_type = 'image/png'

        response = HttpResponse(content_type=content_type)

        extension_list = ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'bmp', 'tif']
        if extension.lower() in extension_list:
            if extension.upper() == 'JPG':
                extension = 'JPEG'
        else:
            extension = 'jpeg'

        im.save(response, extension.upper())

        return response

    try:
        data = open(document_path, 'rb').read()
    except IOError:
        return HttpResponse(status=500)

    return HttpResponse(data, content_type=content_type)


class EditBookPage(LoginRequiredMixin, views.SecurityMixin, TemplateView):

    """Edit Book View which opens up the editor.

    Most of the initial data is loaded from the browser over the Sputnik.
    In the view we just check Basic security permissions and availability
    of the book.
    """

    SECURITY_BRIDGE = BookSecurity
    template_name = 'edit/book_edit.html'
    redirect_unauthorized_user = True
    redirect_field_name = 'redirect'

    def render_to_response(self, context, **response_kwargs):
        # Check for errors
        if context['book'] is None:
            return views.ErrorPage(
                self.request,
                "errors/book_does_not_exist.html",
                {'book_name': context['book_id']}
            )

        if context.get('has_permission', True) is False:
            return views.ErrorPage(
                self.request,
                "errors/editing_forbidden.html",
                {'book': context['book']}
            )

        return super(TemplateView, self).render_to_response(
            context, **response_kwargs)

    def check_permissions(self, request, *args, **kwargs):
        if not self.security.can_edit():
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        try:
            book = models.Book.objects.get(url_title__iexact=kwargs['bookid'])
        except models.Book.DoesNotExist:
            return {'book': None, 'book_id': kwargs['bookid']}

        book_version = book.get_version(None)

        toc = get_toc_for_book(book_version)

        context['request'] = self.request
        context['book'] = book
        context['book_version'] = book_version.get_version()
        context['book_language'] = book.language.abbrevation if book.language else 'en'
        context['security'] = self.security

        try:
            rtl = models.Info.objects.get(book=book, kind=0, name='{http://booki.cc/}dir')
            context['book_dir'] = rtl.get_value().lower()
        except models.Info.DoesNotExist:
            context['book_dir'] = 'ltr'

        context['chapters'] = toc

        # check if we should track changes for current user
        user_permissions = get_user_permissions(self.request.user, book)
        context['track_changes_approve'] = self.security.has_perm('edit.track_changes_approve')
        context['track_changes_enable'] = self.security.has_perm('edit.track_changes_enable')

        should_track_changes = 'edit.track_changes' in user_permissions

        context['track_changes'] = json.dumps(
            book_version.track_changes or should_track_changes)
        context['is_admin'] = self.security.is_admin()
        context['is_owner'] = book.owner == self.request.user
        context['icc_profiles_choices'] = config.get_configuration('ICC_PROFILES_CHOICES', None)

        # publish options are used in panel_publish.html to render available converters
        publish_options = config.get_configuration('PUBLISH_OPTIONS')
        context['publish_options'] = publish_options
        context['page_size_data'] = config.get_configuration('PAGE_SIZE_DATA')


        outputs_map = {}
        converters = convert_loader.find_all(
            module_names=convert_utils.get_converter_module_names())

        for output_key in publish_options:
            # if saved option is not in converters, let's just ignore it
            if output_key not in converters:
                continue

            converter_class = converters[output_key]
            support_section_settings = getattr(converter_class, 'support_section_settings', False)
            if not support_section_settings:
                continue

            safe_key = output_key.replace('-', '_')
            outputs_map[safe_key] = getattr(converter_class, 'verbose_name', output_key)

        context['publish_options_ordered_tuple'] = sorted(outputs_map.items(), key=operator.itemgetter(1))
        context['TocSettings'] = TocSettings

        context['autosave'] = json.dumps({
            'enabled': config.get_configuration('EDITOR_AUTOSAVE_ENABLED'),
            'delay': config.get_configuration('EDITOR_AUTOSAVE_DELAY')
        })
        context['settings_roles_show_permissions'] = config.get_configuration('EDITOR_SETTINGS_ROLES_SHOW_PERMISSIONS')

        context['upload_docx_form'] = UploadDocxFileForm()

        # get book participants
        members_query = self._get_book_participants(book_version)

        from booktype.apps.core.templatetags.booktype_tags import tag_username
        book_members_list = [tag_username(x) for x in members_query]

        # we should also get assigned users to other chapters
        assigned_users = book_version.chapter_set.all().values_list("assigned", flat=True)
        assigned_users = list(assigned_users) + book_members_list

        context['book_members'] = sorted(assigned_users)

        return context

    def _get_book_participants(self, book_version):
        book = book_version.book

        # get all users who have worked on the book
        book_collaborators_ids = models.BookHistory.objects.filter(
            version=book_version, kind=2).values_list('user', flat=True)

        # and also get all users who are members of any role on the book
        book_members = BookRole.objects.filter(book=book).values_list('members', flat=True)

        user_ids = list(book_collaborators_ids) + list(book_members)

        # and of course the book owner
        user_ids.append(book.owner.id)

        return User.objects.filter(id__in=user_ids).distinct()

    def get_login_url(self):
        return reverse('accounts:signin')


class BookHistoryPage(LoginRequiredMixin, JSONResponseMixin,
                      BaseReaderView, ListView):
    model = models.BookHistory
    context_object_name = 'history'
    template_name = 'edit/book_history.html'
    paginate_by = 15

    def get_queryset(self):
        self.book = get_object_or_404(models.Book,
                                      url_title=self.kwargs['bookid'])

        qs = super(BookHistoryPage, self).get_queryset()
        qs = qs.select_related('chapter', 'user', 'book').filter(book=self.book).order_by('-modified')

        # filter by user
        author = self.request.GET.get('user', None)
        if author:
            qs = qs.filter(user__username__in=author.split(','))

        # filter by chapter
        chapter = self.request.GET.get('chapter', None)
        if chapter:
            qs = qs.filter(chapter__title__in=chapter.split(','))

        return qs

    def get(self, request, *args, **kwargs):
        from booktype.apps.reader.templatetags import reader_tags
        history = []
        for item in self.get_queryset():
            activ = reader_tags.verbose_activity(item)
            link_text = item.chapter.title if item.kind == 2 else activ.get('link_text')
            link_url = item.chapter.url_title if item.chapter else ''

            verbose = activ.get('verbose')
            if item.kind == 2:
                verbose = ugettext("Revision {0} saved").format(item.chapter_history.revision)

            history.append({
                'has_link': (item.kind == 2),
                'verbose': verbose,
                'username': activ.get('user').username,
                'modified': activ.get('modified'),
                'formatted': formats.localize(activ.get('modified')),
                'link_text': link_text,
                'link_url': link_url
            })
        return self.render_json_response(history)


class ChapterMixin(BaseReaderView):
    """
    Mixin class that checks if there is a chapter key in kwargs
    and pulls that chapter from database
    """

    def get_context_data(self, **kwargs):
        if 'chapter' in self.kwargs:
            try:
                self.chapter = get_object_or_404(
                    models.Chapter,
                    book=self.object,
                    url_title=self.kwargs['chapter']
                )
            except Http404:
                self.not_found = True
                context = dict(
                    not_found_object=_("Chapter"),
                    object_name=self.kwargs['chapter']
                )
                return context
        kwargs['title'] = self.object.title
        return super(ChapterMixin, self).get_context_data(**kwargs)


class ChapterHistoryPage(LoginRequiredMixin, ChapterMixin, DetailView):
    template_name = "edit/chapter_history.html"

    def get_context_data(self, **kwargs):
        context = super(ChapterHistoryPage, self).get_context_data(**kwargs)
        if self.not_found:
            return context
        context['chapter'] = self.chapter
        context['chapter_history'] = models.ChapterHistory.objects.filter(
            chapter=self.chapter).order_by('-revision')
        context['page_title'] = _('Book History')
        return context


class CompareChapterRevisions(LoginRequiredMixin, ChapterMixin, DetailView):
    model = models.Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    context_object_name = 'book'
    template_name = 'edit/_compare_modal.html'

    def get_context_data(self, **kwargs):
        book = self.get_object()
        rev1 = self.kwargs.get('rev_one', None)
        rev2 = self.kwargs.get('rev_two', None)

        context = super(
            CompareChapterRevisions, self).get_context_data(**kwargs)
        try:
            revision1 = models.ChapterHistory.objects.get(
                chapter__book=book, chapter=self.chapter, revision=rev1)
            revision2 = models.ChapterHistory.objects.get(
                chapter__book=book, chapter=self.chapter, revision=rev2)
        except:
            return context

        context['unified_output'] = unified_diff(revision1.content, revision2.content)
        context['split_output'] = split_diff(revision1.content, revision2.content)
        context['chapter'] = self.chapter
        context['page_title'] = _('Chapter diff')
        context['book'] = book
        context['rev1'] = rev1
        context['rev2'] = rev2
        return context

    def get_template_names(self):
        if not self.request.is_ajax():
            return ["edit/compare_screen.html"]
        return super(CompareChapterRevisions, self).get_template_names()


class RevisionPage(LoginRequiredMixin, views.SecurityMixin, ChapterMixin, DetailView):

    template_name = 'edit/chapter_revision.html'
    http_method_names = [u'post', u'get']
    SECURITY_BRIDGE = security.BookSecurity

    def get_context_data(self, **kwargs):
        context = super(RevisionPage, self).get_context_data(**kwargs)

        if 'revid' in self.kwargs:
            try:
                revision = get_object_or_404(
                    models.ChapterHistory,
                    chapter=self.chapter,
                    revision=self.kwargs['revid']
                )
            except Http404:
                self.not_found = True
                context = dict(
                    not_found_object=_("Revision"),
                    object_name=self.kwargs['revid']
                )
                return context

        context['chapter'] = self.chapter
        context['revision'] = revision
        context['page_title'] = _('Book History | Chapter Revision')
        return context

    def post(self, request, *args, **kwargs):
        book = self.get_object()
        self.object = book
        self.get_context_data(**kwargs)
        book_security = security.get_security_for_book(request.user, book)

        if not book_security.has_perm('edit.history_revert'):
            raise PermissionDenied

        revision = get_object_or_404(
            models.ChapterHistory,
            revision=request.POST["revert"],
            chapter=self.chapter,
            chapter__version=book.version.id
        )

        history = logChapterHistory(
            chapter=self.chapter,
            content=revision.content,
            user=request.user,
            comment=_("Reverted to revision %s.") % revision.revision,
            revision=self.chapter.revision + 1
        )

        if history:
            logBookHistory(
                book=book,
                version=book.version.id,
                chapter=self.chapter,
                chapter_history=history,
                user=request.user,
                args={},
                kind='chapter_save'
            )

        self.chapter.revision += 1
        self.chapter.content = revision.content
        try:
            self.chapter.save()
            messages.success(request, _('Chapter revision successfully reverted.'))
        except:
            messages.warning(request, _('Chapter revision could not be reverted.'))

        url = "{0}#history/{1}".format(
            reverse('edit:editor', args=[book.url_title]),
            self.chapter.url_title
        )
        return HttpResponseRedirect(url)


class BookSettingsView(LoginRequiredMixin, views.SecurityMixin,
                       JSONResponseMixin, BaseReaderView, FormView):

    template_name = 'edit/settings/generic.html'
    SECURITY_BRIDGE = security.BookSecurity

    def camelize(self, text):
        return ''.join([s for s in text.title() if s.isalpha()])

    def dispatch(self, request, *args, **kwargs):
        # check if book exist
        _request_data = getattr(request, request.method)

        bookid = _request_data.get('bookid', None)
        self.book = get_object_or_404(models.Book, id=bookid)

        # a settings option is needed
        option = _request_data.get('setting', None)
        if option and option in VALID_SETTINGS:
            self.submodule = option
        else:
            raise Http404
        return super(BookSettingsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BookSettingsView, self).get_context_data(**kwargs)
        context['option_title'] = VALID_SETTINGS[self.submodule]
        context['option'] = self.submodule
        context['book'] = self.book

        extra_context = self.form_class.extra_context(self.book, self.request)
        if extra_context:
            context.update(extra_context)
        return context

    def get_form_class(self):
        class_text = "%sForm" % self.camelize(self.submodule)
        self.form_class = getattr(book_forms, class_text)
        return self.form_class

    def get_form_kwargs(self):
        kwargs = super(BookSettingsView, self).get_form_kwargs()
        kwargs.update({'book': self.book})
        return kwargs

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()

        # we need this to check if user can see the requested module
        if not form_class.has_perm(self.book, self.request):
            return HttpResponseForbidden()

        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        error = False
        updated_settings = {'submodule': self.submodule, 'settings': None}

        try:
            if form.has_perm(self.book, self.request):
                updated_settings['settings'] = form.save_settings(self.book, self.request)
                message = form.success_message or _('Successfully saved settings.')
            else:
                error, message = True, _('You have no permissions to execute this action.')
        except Exception as err:
            print err
            error, message = True, _('Unknown error while saving changes.')

        return self.render_json_response({'message': unicode(message), 'error': error,
                                          'updated_settings': updated_settings})

    def form_invalid(self, form):
        response = super(BookSettingsView, self).form_invalid(form).render()
        return self.render_json_response({'data': response.content.decode('utf-8'), 'error': True})

    def get_initial(self):
        """
        Returns initial data for each admin option form
        """
        return self.form_class.initial_data(self.book, self.request)

    def get_template_names(self):
        if self.request.is_ajax():
            return [
                "edit/settings/_%s.html" % self.submodule.replace('-', '_'),
                self.template_name
            ]
        return super(BookSettingsView, self).get_template_names()


class DownloadBookHistory(LoginRequiredMixin, DetailView):
    """
    This class is meant to be used for chapterwise history download
    and book history download as well
    """

    # TODO: document how this things work via url and what parameters might take
    # in order to accomplish different things

    model = models.Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    context_object_name = 'book'
    template_name = 'edit/download_history.html'

    DEFAULT_REV = '10'

    ASSETS = {
        'css': [
            'vendor/bootstrap-3.3.7/css/bootstrap.min.css',
            'core/css/booki-new.css'
        ],
        'js': [
            'core/js/jquery-1.9.1.js',
            'vendor/bootstrap-3.3.7/js/transition.js',
            'vendor/bootstrap-3.3.7/js/collapse.js',
            'vendor/bootstrap-3.3.7/js/tooltip.js'
        ]
    }

    def _get_history(self, history_mode):
        book = self.object
        items = self.item_list
        base_revision = self.base_revision

        output = []

        for itm in items:
            revision1 = None

            try:
                revision1 = models.ChapterHistory.objects.filter(
                        chapter__book=book, chapter=itm.chapter
                    ).exclude(revision=itm.chapter.revision).order_by('-modified').first()
                using_revision = revision1.revision
            except models.ChapterHistory.DoesNotExist:
                # if not found and revision was not the default one, just try to pull
                # the default revision we've been using.
                if base_revision not in [self.DEFAULT_REV, '2']:
                    try:
                        revision1 = models.ChapterHistory.objects.get(
                            chapter__book=book, chapter=itm.chapter, revision=self.DEFAULT_REV)
                        using_revision = _("default one ({})").format(self.DEFAULT_REV)
                    except:
                        continue

                if revision1 is None:
                    continue

            except Exception:
                continue

            # do not include latest one because is the current chapter content
            available_revisions = itm.chapter.chapterhistory_set.values_list('revision', flat=True)[1:]
            if len(available_revisions) > 0:
                _revs = ", ".join(map(str, set(available_revisions)))
                available_revisions = _("Available revisions: {}").format(_revs)
            else:
                available_revisions = _("There are no revisions available")

            title = u'{} <small>({} - {}) | <b data-toggle="tooltip" title="{}">{}: {}</b></small>'.format(
                itm.name,
                revision1.modified.strftime('%d.%m.%y %H:%M'),
                itm.chapter.modified.strftime('%d.%m.%y %H:%M'),
                available_revisions,
                _("USING REVISION"),
                using_revision
            )

            if history_mode == 'split':
                content = split_diff(revision1.content, itm.chapter.content)
                if 'class="diff' not in content:
                    content = None
            else:
                content = unified_diff(revision1.content, itm.chapter.content)
                if '<ins>' in content or '<del>' in content:
                    content = "<tr><td valign='top'>%s</td></tr>" % content
                else:
                    content = None

            if content:
                content = self._clean_tags(content)

            output.append({'title': title, 'content': content})

        return output

    def _clean_tags(self, s):
        """
        Remove ins, del and p tags with no content
        we need a more elegant way to achieve this
        """

        s = s.replace('<p></p>', '')
        s = s.replace('<p><br></p>', '')

        s = s.replace('<br><br><br>', '<br>')
        s = s.replace('<br><br>', '<br>')

        s = s.replace('<ins></ins>', '')
        s = s.replace('<del></del>', '')
        s = s.replace('<ins><br></ins>', '')
        s = s.replace('<del><br></del>', '')

        return s

    def get_context_data(self, **kwargs):
        context = super(DownloadBookHistory, self).get_context_data(**kwargs)
        chapterid = self.kwargs.get('chapter', None)
        book_mode = True

        book = context.get('book')
        book_version = book.get_version()
        history_title = book.title

        if chapterid:
            try:
                toc_item = models.BookToc.objects.get(chapter__id=chapterid, book=book)
                history_title = toc_item.chapter.title
                book_mode = False
            except Exception:
                raise Http404

        # both attributes below will be used later to zip both history_modes
        self.item_list = [toc_item] if chapterid else book_version.get_toc()
        self.base_revision = self.request.GET.get('base_rev', self.DEFAULT_REV)

        # pull the diff function based on parameter
        self.history_mode = self.request.GET.get('mode', 'unified')
        context['output'] = self._get_history(self.history_mode)
        context['history_title'] = history_title
        context['book_mode'] = book_mode
        context['html'] = self.request.GET.get('html')
        context['assets'] = self.ASSETS

        return context

    def get_assets_content(self, asset_type):
        """Takes content from assets files to then bundle them into single file"""

        cc = Compressor()
        content = ""

        for f in self.ASSETS.get(asset_type, []):
            filename = cc.get_filename(f)
            content += cc.get_filecontent(filename, 'utf-8')

        if asset_type == 'css':
            content = content.replace('\n', '')
            content = content.replace('\t', '')

        return content

    def render_to_response(self, context, **kwargs):
        response = super(DownloadBookHistory, self).render_to_response(context, **kwargs)

        # allows an html response mode
        if self.request.GET.get('html', False):
            return response

        def _get_name(mode):
            return '{}_history.html'.format(mode)

        content = response.render().content
        zip_name = '{}_history'.format(self.object.url_title)
        history_file_name = _get_name(self.history_mode)

        zfile_content = StringIO.StringIO()
        zfile = zipfile.ZipFile(zfile_content, 'w', zipfile.ZIP_STORED)
        zfile.writestr('{}'.format(history_file_name), content)

        # let's write assets bundle's content
        zfile.writestr('assets/bundle.css', self.get_assets_content('css').encode('utf-8'))
        zfile.writestr('assets/bundle.js', self.get_assets_content('js').encode('utf-8'))

        # include both history modes within zip file
        if self.request.GET.get('zip_both'):
            pending_mode = 'unified' if self.history_mode == 'split' else 'split'
            context['output'] = self._get_history(pending_mode)

            resp = super(DownloadBookHistory, self).render_to_response(context, **kwargs)
            content2 = resp.render().content

            # now it's time to add it to the zip file
            zfile.writestr('{}'.format(_get_name(pending_mode)), content2)

        zfile.close()

        resp = HttpResponse(zfile_content.getvalue(), content_type="application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename={}.zip'.format(zip_name)

        return resp


class InviteCodes(LoginRequiredMixin, views.SecurityMixin, JSONResponseMixin, DetailView, FormView):

    model = models.Book
    slug_field = 'url_title'
    slug_url_kwarg = 'bookid'
    context_object_name = 'book'
    template_name = 'edit/invite_code.html'
    form_class = book_forms.InviteCodeForm

    def get_context_data(self, **kwargs):
        book = self.get_object()
        context = super(InviteCodes, self).get_context_data(**kwargs)
        context['existent_codes'] = book.invite_codes.all()
        return context

    def response(self, data):
        return self.render_json_response(data)

    def form_invalid(self, form):

        return self.response({
            'result': False,
            'errors': form.errors
        })

    def form_valid(self, form):
        instance = form.instance
        instance.book = self.get_object()
        instance.code = str(uuid.uuid4())[:8]
        form.save()

        return self.response({
            'result': True,
            'code': instance.code.upper()
        })
