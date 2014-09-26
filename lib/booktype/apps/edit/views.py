# -*- coding: utf-8 -*- 

import re
import json
import uuid
import hashlib
import difflib
import datetime
import mimetypes
import unidecode

from django.utils import formats
from django.conf import settings
from django.db import transaction
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, DetailView, FormView
from django.http import Http404, HttpResponse, HttpResponseRedirect

from braces.views import (LoginRequiredMixin, UserPassesTestMixin,
                          JSONResponseMixin)

from booki.editor import models
from booki.utils.log import logChapterHistory, logBookHistory

from booktype.utils import security
from booktype.apps.core import views
from booktype.utils.misc import booktype_slugify
from booktype.apps.reader.views import BaseReaderView

from .utils import color_me
from .channel import get_toc_for_book
from . import forms as book_forms


VALID_SETTINGS = {
    'language': _('Book Language')
}

getTOCForBook = get_toc_for_book

@login_required
@transaction.commit_manually
def upload_attachment(request, bookid, version=None):
    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.get_version(version)

    stat = models.BookStatus.objects.filter(book = book)[0]

    operationResult = True

    # check this for transactions
    try:
        fileData = request.FILES['files[]']
        att = models.Attachment(version = book_version,
                                # must remove this reference
                                created = datetime.datetime.now(),
                                book = book,
                                status = stat)
        att.save()

        attName, attExt = os.path.splitext(fileData.name)
        att.attachment.save('{}{}'.format(booktype_slugify(attName), attExt), fileData, save = False)
        att.save()

        # TODO:
        # must write info about this to log!
    # except IOError:
    #     operationResult = False
    #     transaction.rollback()
    except:
        oprerationResult = False
        transaction.rollback()
    else:
       # maybe check file name now and save with new name
       transaction.commit()


    response_data = {"files":[{"url":"http://127.0.0.1/",
                                "thumbnail_url":"http://127.0.0.1/",
                                "name":"boot.png",
                                "type":"image/png",
                                "size":172728,
                                "delete_url":"",
                                "delete_type":"DELETE"}]}


    if "application/json" in request.META['HTTP_ACCEPT']:
        return HttpResponse(json.dumps(response_data), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(response_data), mimetype="text/html")


@login_required
@transaction.commit_manually
def upload_cover(request, bookid, version=None):
    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
    
    # check this for transactions
    try:
        fileData = request.FILES['files[]']
        title = request.POST.get('title', '')
        try:
            filename = unidecode.unidecode(fileData.name)
        except:
            filename = uuid.uuid1().hex

        h = hashlib.sha1()
        h.update(filename)
        h.update(title)
        h.update(str(datetime.datetime.now()))

        license = models.License.objects.get(abbrevation=request.POST.get('license', ''))

        cover = models.BookCover(
            book = book,
            user = request.user,
            cid = h.hexdigest(),
            title = title,
            filename = filename[:250],
            width = 0,
            height = 0,
            unit = request.POST.get('unit', 'mm'),
            booksize = request.POST.get('booksize', ''),
            cover_type = request.POST.get('type', ''),
            creator = request.POST.get('creator', '')[:40],
            license = license,
            notes = request.POST.get('notes', '')[:500],
            approved = False,
            is_book = False,
            is_ebook = True,
            is_pdf = False,
            created = datetime.datetime.now()
        )
        cover.save()
        
        # now save the attachment
        cover.attachment.save(filename, fileData, save=False)
        cover.save()
    except:
        transaction.rollback()
    else:
       transaction.commit()

    response_data = {
        "files": [{ 
            "url":"http://127.0.0.1/",
            "thumbnail_url":"http://127.0.0.1/",
            "name":"boot.png",
            "type":"image/png",
            "size":172728,
            "delete_url":"",
            "delete_type":"DELETE"
            }]
        }

    if "application/json" in request.META['HTTP_ACCEPT']:
        return HttpResponse(json.dumps(response_data), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(response_data), mimetype="text/html")


def cover(request, bookid, cid, fname = None, version=None):

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    try:
        cover = models.BookCover.objects.get(cid = cid)
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

    content_type = mimetypes.types_map.get('.'+extension, 'binary/octet-stream')

    if request.GET.get('preview', '') == '1':
        try:
            from PIL import Image
        except ImportError:
            import Image

        try:
            if extension.lower() in ['pdf', 'psd', 'svg']:
                raise

            im = Image.open(cover.attachment.name)
            im.thumbnail((300, 200), Image.ANTIALIAS)
        except:
            try:
                im = Image.open('%s/editor/images/booktype-cover-%s.png' % (settings.STATIC_ROOT, extension.lower()))
                extension = 'png'
                content_type = 'image/png'
            except:
                # Not just IOError but anything else
                im = Image.open('%s/editor/images/booktype-cover-error.png' % settings.STATIC_ROOT)
                extension = 'png'
                content_type = 'image/png'

        response = HttpResponse(content_type=content_type)

        if extension.lower() in ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'bmp', 'tif']:
            if extension.upper() == 'JPG': extension = 'JPEG'
        else:
            extension = 'jpeg'

        im.save(response, extension.upper())

        return response

    try:
        data = open(document_path, 'rb').read()
    except IOError:
        return HttpResponse(status=500)

    return HttpResponse(data, content_type=content_type)


class EditBookPage(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Basic Edito Book View which opens up the editor. 

    Most of the initial data is loaded from the browser over the Sputnik. In the view we just check Basic
    security permissions and availability of the book.
    """

    template_name = 'edit/book_edit.html'
    redirect_unauthorized_user = True
    redirect_field_name = 'redirect'

    def render_to_response(self, context, **response_kwargs):
        # Check for errors
        if context['book'] == None:
            return views.ErrorPage(self.request, "errors/book_does_not_exist.html", {'book_name': context['book_id']})

        if context.get('has_permission', True) == False:
            return views.ErrorPage(self.request, "errors/editing_forbidden.html", {'book': context['book']})    

        return super(TemplateView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemplateView, self).get_context_data(**kwargs)

        try:
            book = models.Book.objects.get(url_title__iexact=kwargs['bookid'])
        except models.Book.DoesNotExist:
            return {'book': None, 'book_id': kwargs['bookid']}

        book_version = book.get_version(None)

        book_security = security.get_user_security_for_book(self.request.user, book)
        has_permission = security.can_edit_book(book, book_security)

        if not has_permission:
            return {'book': book, 'has_permission': False}

        toc = get_toc_for_book(book_version)

        context['request'] = self.request
        context['book'] = book
        context['book_version'] = book_version.get_version()

        context['chapters'] = toc        

        context['base_url'] = settings.BOOKTYPE_URL
        context['static_url'] = settings.STATIC_URL
        context['is_admin'] = book_security.is_group_admin() or book_security.is_book_admin() or book_security.is_superuser()
        context['is_owner'] = book.owner == self.request.user

        return context

    def test_func(self, user):
        """Filters list of user who can and who can not edit the book.

        This does not do much at the moment but is left for the future use. 
        """

        return True

    def get_login_url(self):
        return reverse('accounts:signin')


class BookHistoryPage(LoginRequiredMixin, JSONResponseMixin, BaseReaderView, ListView):
    model = models.BookHistory
    context_object_name = 'history'
    template_name = 'edit/book_history.html'
    paginate_by = 15

    def get_queryset(self):
        self.book = get_object_or_404(models.Book, url_title=self.kwargs['bookid'])
        qs = super(BookHistoryPage, self).get_queryset().filter(book=self.book).order_by('-modified')

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

            history.append({
                'has_link': (item.kind == 2),
                'verbose': activ.get('verbose'),
                'username': activ.get('user').username,
                'modified': activ.get('modified'),
                'formatted': formats.localize(activ.get('modified')),
                'link_text': link_text,
                'link_url': link_url
            })
        return self.render_json_response(history)


class ChapterMixin(BaseReaderView):
    # TODO: add docstrings

    def get_context_data(self, **kwargs):
        if 'chapter' in self.kwargs:
            try:
                self.chapter = get_object_or_404(models.Chapter, book=self.object, url_title=self.kwargs['chapter'])
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
        context['chapter_history'] = models.ChapterHistory.objects.filter(chapter=self.chapter).order_by('-revision')
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
        params = self.request.GET
        rev1 = params.get('rev1', None)
        rev2 = params.get('rev2', None)

        context = super(CompareChapterRevisions, self).get_context_data(**kwargs)
        revision1 = models.ChapterHistory.objects.get(chapter__book=book, chapter=self.chapter, revision=rev1)
        revision2 = models.ChapterHistory.objects.get(chapter__book=book, chapter=self.chapter, revision=rev2)

        output = []

        output_left = '<td valign="top">'
        output_right = '<td valign="top">'
        
        content1 = re.sub('<[^<]+?>', '', revision1.content.replace('<p>', '\n<p>').replace('. ', '. \n')).splitlines(1)
        content2 = re.sub('<[^<]+?>', '', revision2.content.replace('<p>', '\n<p>').replace('. ', '. \n')).splitlines(1)

        lns = [line for line in difflib.ndiff(content1, content2)]

        n = 0
        minus_pos = None
        plus_pos = None

        def my_find(s, wh, x = 0):
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
                if n+1 < len(lns) and lns[n+1][0] == '?':
                    lns[n+1] += lns[n+1] + ' '

                    x = my_find(lns[n+1][2:], '+?^-')
                    y = lns[n+1][2:].find(' ', x)-2

                    plus_pos = (x, y)
                else:
                    plus_pos = None

                output_right += '<div class="diff changed">'+color_me(line[2:], 'diff added', plus_pos)+'</div>'
                output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')
                output_left = output_right = '<td valign="top">'
            elif line[:2] == '- ':
                if n+1 < len(lns) and lns[n+1][0] == '?':
                    lns[n+1] += lns[n+1] + ' '

                    x = my_find(lns[n+1][2:], '+?^-')
                    y = lns[n+1][2:].find(' ', x)-2

                    minus_pos = (x, y)
                else:
                    minus_pos = None

                output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')

                output_left = output_right = '<td valign="top">'
                output_left +=  '<div class="diff changed">'+color_me(line[2:], 'diff deleted', minus_pos)+'</div>'
            elif line[:2] == '  ':
                if line[2:].strip() != '':
                    output_left  += line[2:]+'<br/><br/>'
                    output_right += line[2:]+'<br/><br/>'

            n += 1

        output.append('<tr>'+output_left+'</td>'+output_right+'</td></tr>')
        output = [mark_safe(o) for o in output]

        context['output'] = output
        context['rev1'] = rev1
        context['rev2'] = rev2
        return context


class RevisionPage(LoginRequiredMixin, ChapterMixin, DetailView):
    template_name = 'edit/chapter_revision.html'

    http_method_names = [u'post', u'get']
    
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

        revision = get_object_or_404(
            models.ChapterHistory,
            revision=request.POST["revert"], 
            chapter=self.chapter, 
            chapter__version=book.version.id
        )

        history = logChapterHistory(
            chapter = self.chapter,
            content = revision.content,
            user = request.user,
            comment = _("Reverted to revision %s.") % revision.revision,
            revision = self.chapter.revision+1
        )

        if history:
            logBookHistory(
                book = book,
                version = book.version.id,
                chapter = self.chapter,
                chapter_history = history,
                user = request.user,
                args = {},
                kind = 'chapter_save'
            )

        self.chapter.revision += 1
        self.chapter.content = revision.content;
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

class BookSettingsView(LoginRequiredMixin, JSONResponseMixin, BaseReaderView, FormView):

    template_name = 'edit/_settings_form.html'

    def camelize(self, text):
        return ''.join([s for s in text.title() if s.isalpha()])

    def dispatch(self, request, *args, **kwargs):
        # check if book exist
        bookid = request.REQUEST.get('bookid', None)
        self.book = get_object_or_404(models.Book, id=bookid)

        # a settings option is needed
        option = request.REQUEST.get('setting', None)
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
        return context

    def get_form_class(self):
        class_text = "%sForm" % self.camelize(self.submodule)
        self.form_class = getattr(book_forms, class_text)
        return self.form_class

    def form_valid(self, form):
        try:
            form.save_settings(self.book, self.request)
            error, message = False, form.success_message or _('Successfully saved settings.')
        except Exception as err:
            print err
            error, message = True, _('Unknown error while saving changes.')
        return self.render_json_response({'message': unicode(message), 'error': error})

    def form_invalid(self, form):
        response = super(BookSettingsView, self).form_invalid(form).render()        
        return self.render_json_response({'data': response.content, 'error': True})

    def get_initial(self):
        """
        Returns initial data for each admin option form
        """
        return self.form_class.initial_data(self.book, self.request)
