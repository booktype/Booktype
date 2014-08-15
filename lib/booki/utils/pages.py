from django.shortcuts import render_to_response

from booktype.apps.core import views

ErrorPage = views.ErrorPage

def profileinfo(request, profileid):
    """
    Returns formated profile page. Used for the tooltip info.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type profileid: C{string}
    @param profileid: Unique Booki username
    """
    
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
    """
    Returns formated attachment info page. Used for the tooltip info.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Booki name
    @type version: C{string}
    @param version: Booki version
    @type attachment: C{string}
    @param attachment: Attachment name
    """

    from booki.editor import models
    from booki.editor.views import getVersion

    book = models.Book.objects.get(url_title__iexact=bookid)
    book_version = getVersion(book, version)
    att = None

    # very stupid
    for a in book_version.getAttachments():
        if a.getName() == attachment:
            att = a

    return render_to_response('booki/attachmentinfo.html', {"book": book,
                                                            "attachment_name": attachment, 
                                                            "attachment": att,
                                                            "request": request
                                                        }
                              )