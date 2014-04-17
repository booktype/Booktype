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
from django.views.generic.base import TemplateView, RedirectView

from booki.portal import feeds


urlpatterns = patterns('',
                   # groups
                   url(r'^bookigroups/(?P<groupid>[\w\s\_\.\-]+)/add_book/$', 'booki.portal.views.add_book'),                    
                   url(r'^bookigroups/(?P<groupid>[\w\s\_\.\-]+)/remove_book/$', 'booki.portal.views.remove_book'),                                       
                   url(r'^bookigroups/(?P<groupid>[\w\s\_\.\-]+)/$', 'booki.portal.views.view_group', name="view_group"),                    

                   # feeds
                   url(r'^feeds/rss/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedRSS()),
                   url(r'^feeds/atom/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedAtom()),
                   url(r'^feeds/rss/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedRSS()),
                   url(r'^feeds/atom/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedAtom()),
                   url(r'^feeds/rss/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedRSS()),
                   url(r'^feeds/atom/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedAtom()),

                   # front page listing views
                   url(r'list-groups/', 'booki.portal.views.view_groups', name='list_groups'),
                   url(r'list-books/', 'booki.portal.views.view_books', name='list_books'),
                   url(r'list-people/', 'booki.portal.views.view_people', name='list_people'),

                   # favicon 
                   (r'^favicon\.ico', RedirectView.as_view(url='/static/profile/images/favicon.png')),
                   (r'^robots.txt$', TemplateView.as_view(template_name='robots.txt')), #, mimetype='text/plain')), 

                   # json booklist for objavi
                   # TODO: remove this
                   #url(r'^list-books.json$', 'booki.editor.views.view_books_json'),

                   # list of books by ID
                   #url(r'^list-books-by-id/(?P<scheme>[\w. -]+).json?$', 'booki.portal.views.view_books_by_id'),

)
