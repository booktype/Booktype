# -*- coding: utf-8 -*- 

import datetime

from braces.views import LoginRequiredMixin, UserPassesTestMixin

from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.conf import settings

from booki.utils import log
from booki.editor import models
from booktype.apps.core import views
from booktype.utils import security

def get_toc_for_book(version):
    results = []
    for chap in version.get_toc():
        # is it a section or chapter?
        if chap.chapter:
            results.append((chap.chapter.id,
                            chap.chapter.title,
                            chap.chapter.url_title,
                            chap.typeof,
                            chap.chapter.status.id))
        else:
            results.append(('s%s' % chap.id, chap.name, chap.name, chap.typeof))
    return results

getTOCForBook = get_toc_for_book


@login_required
@transaction.commit_manually
def upload_attachment(request, bookid, version=None):
    import json
    import datetime
    import os.path

    from booktype.utils.misc import booktype_slugify

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
    import json
    import datetime

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return views.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = book.get_version(version)

    operationResult = True

    # check this for transactions
    try:
        fileData = request.FILES['files[]']

        title = request.POST.get('title', '')

        import hashlib

        h = hashlib.sha1()
        h.update(fileData.name)
        h.update(title)
        h.update(str(datetime.datetime.now()))

        license = models.License.objects.get(abbrevation=request.POST.get('license', ''))

        try:
            filename = unidecode.unidecode(fileData.name)
        except:
            filename = ''

        cov = models.BookCover(book = book,
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
                               created = datetime.datetime.now())
        cov.save()
        
        cov.attachment.save(fileData.name, fileData, save = False)
        cov.save()

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


def cover(request, bookid, cid, fname = None, version=None):
    from django.views import static

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

    import mimetypes
    mimetypes.init()

    extension = cover.filename.split('.')[-1].lower()

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

    response = HttpResponse(data, content_type=content_type)
    return response


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
