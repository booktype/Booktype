# This file is part of Booktype.
# Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

from django.contrib.auth.decorators import login_required
from django.conf.urls import patterns, url, include

from .views import EditBookPage

urlpatterns = patterns('',                      
                       url(r'^_upload/$', 'booktype.apps.edit.views.upload_attachment', name='upload_attachment'),
                       url(r'^_upload_cover/$', 'booktype.apps.edit.views.upload_cover', name='upload_cover'),
                       url(r'^_cover/(?P<cid>[\w\s\_\d\.\-]+)/(?P<fname>.*)$',  'booktype.apps.edit.views.cover', name='view_cover'),
                       url(r'^_edit/static/(?P<attachment>.*)$', 'booktype.apps.core.views.staticattachment'),
                       url(r'^_edit/$', EditBookPage.as_view(), name='editor')
                      )
