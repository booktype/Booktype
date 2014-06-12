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

from django.conf.urls import patterns, url, include


urlpatterns = patterns('',
                        # utility views                      
                        url(r'^_utils/thumbnail/(?P<attachment>.*)$',  'booki.editor.views.thumbnail_attachment', name='thumbnail_attachment'),                                                url(r'^_cover/(?P<cid>[\w\s\_\d\.\-]+)/(?P<fname>.*)$',  'booki.editor.views.view_cover', name='view_cover'),

                        # upload
                        url(r'^_upload/$',  'booki.editor.views.upload_attachment', name='upload_attachment'),
                        url(r'^_upload_cover/$',  'booki.editor.views.upload_cover', name='upload_cover'),

                        # book editing
                        url(r'^_edit/$', 'booki.editor.views.edit_book', name='edit_book'),
                        url(r'^_edit/static/(?P<attachment>.*)$', 'booktype.apps.core.views.staticattachment'),
                        url(r'^_edit/book-list.json$', 'booki.editor.views.view_books_autocomplete'),
                      )       
