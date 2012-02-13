# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response


def ErrorPage(request, templateFile, args = {}, status=200, content_type='text/html'):
    """
    Returns nicely formated Error page.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type templateFile: C{string}
    @param templateFile: Path to template file
    @type args: C{dict}
    @param args: Additional arguments we want to pass to the template
    @type status: C{int}
    @param status: HTTP return code
    @type content_type: C{string}
    @param content_type: Content-Type for the response
    """
    
    t = loader.get_template(templateFile)
    c = RequestContext(request, args)

    return HttpResponse(t.render(c), status=status, content_type=content_type)    


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
