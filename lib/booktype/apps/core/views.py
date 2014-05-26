import re

from django.views.generic import TemplateView
from django.views import static
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib import auth

from booki.utils.misc import isValidEmail
from booki.editor.models import Book


class BasePageView(object):
    page_title = ''
    title = ''

    def get_context_data(self, **kwargs):
        context = super(BasePageView, self).get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["title"] = self.title
        context["request"] = self.request

        return context


class PageView(BasePageView, TemplateView):
    pass


def staticattachment(request, bookid, attachment, version=None, chapter=None):
    """
    Django View. Returns content of an attachment.

    @todo: It is wrong in so many different levels to serve attachments this way.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type attachment: C{string}
    @param attachment: Name of the attachment
    @type version: C{string}
    @param version: Version of the book
    """

    book = get_object_or_404(Book, url_title__iexact=bookid)
    book_version = book.getVersion(version)
    path = '%s/%s' % (book_version.getVersion(), attachment)
    document_root = '%s/books/%s/' % (settings.DATA_ROOT, bookid)

    return static.serve(request, path, document_root)


def _checkIfEmpty(request, key):
    return request.POST.get(key, "").strip() == ""


def _doChecksForEmpty(request):
    if _checkIfEmpty(request, "username"):
        return 2
    if _checkIfEmpty(request, "email"):
        return 3
    if _checkIfEmpty(request, "password") or _checkIfEmpty(request, "password2"):
        return 4
    if _checkIfEmpty(request, "fullname"):
        return 5

    return 0


def _doCheckValid(request):
    # check if it is valid username
    # - from 2 to 20 characters long
    # - word, number, ., _, -
    mtch = re.match('^[\w\d\_\.\-]{2,20}$', request.POST.get("username", "").strip())
    if not mtch:
        return 6

    # check if it is valid email
    if not bool(isValidEmail(request.POST["email"].strip())):
        return 7

    if request.POST.get("password", "") != request.POST.get("password2", "").strip():
        return 8
    if len(request.POST.get("password", "").strip()) < 6:
        return 9

    if len(request.POST.get("fullname", "").strip()) > 30:
        return 11

    # check if this user exists
    try:
        u = auth.models.User.objects.get(username=request.POST.get("username", "").strip())
        return 10
    except auth.models.User.DoesNotExist:
        pass

    return 0