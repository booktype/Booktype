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

from django.conf.urls import url

from booktype.apps.portal import feeds
from .views import (
    FrontPageView, GroupPageView, AllGroupsPageView, PeoplePageView,
    BooksPageView, GroupUpdateView, GroupCreateView, AddBooksView,
    GroupDeleteView, RemoveBookView
)


urlpatterns = [
    url(r'^$', FrontPageView.as_view(), name='frontpage'),
    url(r'^groups/_create/$', GroupCreateView.as_view(), name='group_create'),
    url(r'^groups/_settings/(?P<groupid>[\w\s\_\.\-]+)/$', GroupUpdateView.as_view(), name='group_settings'),
    url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/$', GroupPageView.as_view(), name='group'),
    url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/add_book/$', AddBooksView.as_view(), name='add_book'),
    url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/delete/$', GroupDeleteView.as_view(), name='delete_group'),
    url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/(?P<bookid>[\w\s\_\.\-]+)/remove/$',
        RemoveBookView.as_view(), name='remove_book'),

    url(r'^list-groups/$', AllGroupsPageView.as_view(), name='list_groups'),
    url(r'^list-people/$', PeoplePageView.as_view(), name='list_people'),
    url(r'^list-books/$', BooksPageView.as_view(), name='list_books'),

    # feeds
    url(r'^feeds/rss/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedRSS(), name='feeds_rss_book'),
    url(r'^feeds/atom/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedAtom(), name='feeds_atom_book'),
    url(r'^feeds/rss/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedRSS(),
        name='feeds_rss_chapter'),
    url(r'^feeds/atom/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedAtom(),
        name='feeds_atom_chapter'),

    # user feeds commented temporary
    # url(r'^feeds/rss/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedRSS()),
    # url(r'^feeds/atom/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedAtom()),
]
