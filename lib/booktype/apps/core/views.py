from django.views.generic import TemplateView
from django.views import static
from django.shortcuts import get_object_or_404
from django.conf import settings

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


def staticattachment(request, bookid,  attachment, version=None, chapter = None):
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