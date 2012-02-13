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

def remote_message_send(request, message, bookid):        
    """
    Called when user is sending message to chat channel L{bookid}.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    """
    
    import sputnik

    sputnik.addMessageToChannel(request, "/chat/%s/" % bookid, {"command": "message_received", "from": request.user.username, "message": message["message"]})
    return {}
