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

from booktype.apps.portal import feeds
from .views import FrontPageView, GroupPageView, AllGroupsPageView, GroupSettingsPageView, PeoplePageView
from .views import BooksPageView, AddBooksView


urlpatterns = patterns(
    '',
    url(r'^$', FrontPageView.as_view(), name='frontpage'),
    url(r'^bookigroups/(?P<groupid>[\w\s\_\.\-]+)/$', 'booki.portal.views.view_group', name="view_group"),
    url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/$', GroupPageView.as_view(), name='group'),
    url(r'^groups/_settings/(?P<groupid>[\w\s\_\.\-]+)/$', GroupSettingsPageView.as_view(), name='group_settings'),
    url(r'^list-groups/$', AllGroupsPageView.as_view(), name='list_groups'),
    url(r'^list-people/$', PeoplePageView.as_view(), name='list_people'),
    url(r'^list-books/$', BooksPageView.as_view(), name='list_books'),
    url(r'^bookigroups/(?P<groupid>[\w\s\_\.\-]+)/add_book/$', AddBooksView.as_view(), name='add_book'),

    # feeds
    url(r'^feeds/rss/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedRSS()),
    url(r'^feeds/atom/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedAtom()),
    url(r'^feeds/rss/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedRSS()),
    url(r'^feeds/atom/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedAtom()),
    url(r'^feeds/rss/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedRSS()),
    url(r'^feeds/atom/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedAtom()),
)
