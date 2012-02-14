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

from django.db import transaction

from django.conf import settings

try:
    STATUS_URL = settings.STATUS_URL
except AttributeError:
    STATUS_URL = 'http://status.flossmanuals.net/'


def remote_get_status_messages(request, message, profileid):
    """
    Fetches RSS feed from status.net and returns its content. 

    Output:
     - list

    @todo: Not used anymore. Probably should remove it.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type profileid: C{string}
    @param profile: Unique Profile id
    @rtype: C{dict}
    @return: Returns feed content
    """

    return {}
#    import feedparser
#
#    d = feedparser.parse('%s%s/rss' % (STATUS_URL, profileid))
#
#    messages = [(x['content'][0]['value'], ) for x in d['entries']]
#
#    return {"list": messages}

def remote_group_create(request, message, profileid):
    """
    Creates new Booki Group.

    Input:
     - groupName
     - groupDescription

    Output:
     - list

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type profileid: C{string}
    @param profile: Unique Profile id
    @rtype: C{dict}
    @return: Returns success of the command
    """

    from booki.utils.book import createBookiGroup, BookiGroupExist

    groupName = message.get("groupName", "")
    groupDescription = message.get("groupDescription", "")

    try:
        group = createBookiGroup(groupName, groupDescription, request.user)
        group.members.add(request.user)
    except BookiGroupExist:
        transaction.rollback()
        return {"created": False}
    else:
        transaction.commit()

    return {"created": True}


def remote_init_profile(request, message, profileid):
    """
    Initializes data.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type profileid: C{string}
    @param profile: Unique Profile id
    """

    import sputnik

    ## get online users
    try:
        _onlineUsers = sputnik.smembers("sputnik:channel:%s:users" % message["channel"])
    except:
        _onlineUsers = []

    if request.user.username not in _onlineUsers:
        try:
            sputnik.sadd("sputnik:channel:%s:users" % message["channel"], request.user.username)
        except:
            pass

    return {}


def remote_mood_set(request, message, profileid):
    """
    Sets new mood for this profile.

    Input:
     - value

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type profileid: C{string}
    @param profile: Unique Profile id
    """

    # should check permissions
    from django.utils.html import strip_tags

    ## maximum size is 30 characters only
    ## html tags are removed
    moodMessage = strip_tags(message.get("value",""))[:30]

    import booki.account.signals
    booki.account.signals.account_status_changed.send(sender = request.user, message = message.get('value', ''))

    # save new permissions
    profile = request.user.get_profile()
    profile.mood = moodMessage

    try:
        profile.save()
    except:
        transaction.rollback()
    else:
        transaction.commit()

        ## propagate to other users
        ## probably should only send it to /booki/ channel
        
        import sputnik

        for chnl in sputnik.smembers("sputnik:channels"):
            if sputnik.sismember("sputnik:channel:%s:users" % message['channel'], request.user.username):
                sputnik.addMessageToChannel(request, chnl, {"command": "user_status_changed", 
                                                            "from": request.user.username, 
                                                            "message": moodMessage}, 
                                            myself=True)
            
    return {}

def remote_hide_book(request, message, profileid):
    from booki.editor import models

    book = models.Book.objects.get(url_title = message["bookID"])

    if message["action"] == "hide":
        book.hidden = True
    else:
        book.hidden = False

    book.save()
    transaction.commit()

    return {"result": True}

def remote_load_info(request, message, profileid):
    from django.utils.html import escape

    user    = request.user
    profile = request.user.get_profile()
    description = escape(profile.description).replace('\r', '')

    lines = description.split('\n')

    import django.template.loader
    from django.template import Context

    c = Context({"user": request.user})
    tmpl = django.template.loader.get_template_from_string("{% load profile %}{% profile_image  user %}") 
    html = tmpl.render(c)

    
    info = {'username': user.username,
            'fullname': user.first_name,
            'description': '<br/>'.join(lines),
            'image': html
        }

    return {"result": True, "info": info}
