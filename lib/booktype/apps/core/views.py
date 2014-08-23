from django.views.generic import TemplateView
from django.views import static
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.shortcuts import RequestContext
from django.conf import settings
from django.template import loader
from django.http import HttpResponse

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


def staticattachment(request, bookid,  attachment, version=None, chapter = None, revid = None):
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


def ErrorPage(request, template_file, args={}, status=200, content_type='text/html'):
    """
    Returns nicely formated Error page.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type template_file: C{string}
    @param template_file: Path to template file
    @type args: C{dict}
    @param args: Additional arguments we want to pass to the template
    @type status: C{int}
    @param status: HTTP return code
    @type content_type: C{string}
    @param content_type: Content-Type for the response
    """

    t = loader.get_template(template_file)
    c = RequestContext(request, args)

    return HttpResponse(t.render(c), status=status, content_type=content_type)


def error404(request):
    return render(request, 'errors/404.html')


def error500(request):
    return render(request, 'errors/500.html')


def error403(request):
    return render(request, 'errors/403.html')


def error400(request):
    return render(request, 'errors/400.html')    