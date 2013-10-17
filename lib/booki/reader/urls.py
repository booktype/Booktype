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

from django.conf.urls import patterns, url, include

from booki.portal import feeds


urlpatterns = patterns('',
                      # full view
                      url(r'^_full/$', 'booki.reader.views.view_full', name='view_full'),                       

                      # info pages 
                      url(r'^_info/$', 'booki.reader.views.book_info', name='book_info'),
                      url(r'^_info/cover.jpg$', 'booki.reader.views.book_cover', name='book_cover'),
                      url(r'^_info/edit/$', 'booki.reader.views.edit_info', name='edit_info'),
                      url(r'^_info/delete/$', 'booki.reader.views.book_delete', name='book_delete'),

                      # draft view
                      #url(r'^_draft/static/(?P<attachment>.*)$',  'booki.reader.views.attachment', name='view_attachment'),
                      url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.draft_chapter', name='draft_chapter'),
                      url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
                      url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment', name='draft_attachment'),
                      url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/$', 'booki.reader.views.draft_book', name='draft_book'),
                      url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.draft_chapter', name='draft_chapter'),
                      url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
                      url(r'^_draft/$', 'booki.reader.views.draft_book', name='draft_book'),

                      # book view
                      url(r'^(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.book_chapter', name='book_chapter'),
                      url(r'^(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
                      url(r'^$', 'booki.reader.views.book_view', name='book_view')
                      )
