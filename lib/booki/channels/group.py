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

from booki.editor import models
from booki.utils import security

def remote_get_status_messages(request, message, groupid):
    from booki.statusnet.models import searchMessages

    group = models.BookiGroup.objects.get(url_name=groupid)

    mess = searchMessages('%%23%s' % group.url_name)
    # remove this hard code
    messages = ['<a href="http://status.flossmanuals.net/notice/%s">%s: %s</a>' % (m['id'], m['from_user'], m['text']) for m in mess['results']]

    return {"list": messages}


def remote_init_group(request, message, groupid):
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

def remote_leave_group(request, message, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.remove(request.user)
    transaction.commit()

    return {"result": True}

def remote_join_group(request, message, groupid):
    group = models.BookiGroup.objects.get(url_name=groupid)
    group.members.add(request.user)
    transaction.commit()

    return {"result": True}
