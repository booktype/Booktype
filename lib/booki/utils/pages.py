from django.http import HttpResponse
from django.template import RequestContext, loader


def ErrorPage(request, templateFile, args = {}, status=200, content_type='text/html'):
    t = loader.get_template(templateFile)
    c = RequestContext(request, args)

    return HttpResponse(t.render(c), status=status, content_type=content_type)    

