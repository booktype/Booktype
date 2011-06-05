from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response


def ErrorPage(request, templateFile, args = {}, status=200, content_type='text/html'):
    t = loader.get_template(templateFile)
    c = RequestContext(request, args)

    return HttpResponse(t.render(c), status=status, content_type=content_type)    


def profileinfo(request, profileid):
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(username=profileid)
    except User.DoesNotExist:
        user = None

    return render_to_response('booki/userinfo.html', {"user": user,
                                                      "profile": user.get_profile(),
                                                      "request": request
                                                        }
                              )

def attachmentinfo(request, bookid, version, attachment):
    from booki.editor import models
    from booki.editor.views import getVersion

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)
    att = None

    # very stupid
    for a in book_version.getAttachments():
        print a
        if a.getName() == attachment:
            att = a

    return render_to_response('booki/attachmentinfo.html', {"book": book,
                                                            "attachment_name": attachment, 
                                                            "attachment": att,
                                                            "request": request
                                                        }
                              )
