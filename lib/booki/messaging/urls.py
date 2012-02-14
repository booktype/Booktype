# This file is part of Booktype.
# Copyright (c) 2012  Seravo Oy <tuukka@seravo.fi>
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


from django.conf.urls.defaults import *

urlpatterns = patterns('booki.messaging.views',
    (r'^post$', 'view_post'),
    (r'^follow$', 'view_follow'),
    (r'^unfollow$', 'view_unfollow'),
    (r'^tags/([\w]+)$', 'view_tag', None, 'view_tag'),
)
