# This file is part of Booktype.
# Copyright (c) 2014 Helmy Giacoman <helmy.giacoman@sourcefabric.org>
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

from django.conf.urls import patterns, url

from .views import InfoPageView, DeleteBookView, EditBookInfoView
from .views import DraftChapterView, FullView, BookCoverView, PublishedBookView

urlpatterns = patterns('',
   url(r'^$', PublishedBookView.as_view(), name='published_book'),
   url(r'^_info/$', InfoPageView.as_view(), name='infopage'),
   url(r'^_info/cover.jpg$', BookCoverView.as_view(), name='book_cover'),
   url(r'^_info/edit/$', EditBookInfoView.as_view(), name='edit_info_book'),
   url(r'^_info/delete/$', DeleteBookView.as_view(), name='delete_book'),
   url(r'^_full/$', FullView.as_view(), name='full_view'),

   # draft book page
   url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/$', DraftChapterView.as_view(), name='draft_chapter_page'),
   url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booktype.apps.core.views.staticattachment'),
   url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/static/(?P<attachment>.*)$', 'booktype.apps.core.views.staticattachment', name='draft_attachment'),
   url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/$', DraftChapterView.as_view(), name='draft_chapter_page'),
   url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/$', DraftChapterView.as_view(), name='draft_chapter_page'),
   url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booktype.apps.core.views.staticattachment'),
   url(r'^_draft/static/(?P<attachment>.*)$', 'booktype.apps.core.views.staticattachment'),
   url(r'^_draft/$', DraftChapterView.as_view(), name='draft_chapter_page'),
)