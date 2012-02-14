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

from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()


if settings.BOOKI_MAINTENANCE_MODE:
    urlpatterns = patterns('',
                           url(r'^admin/', include(admin.site.urls)),
                           url(r'^.*$', 'booki.portal.views.maintenance', name='maintenance')
                           )
else:
    from booki.portal import feeds

    urlpatterns = patterns('',
                           # administration
                           # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                           url(r'^admin/', include(admin.site.urls)),

                           # front page                       
                           url(r'^$', 'booki.portal.views.view_frontpage', name="frontpage"),

                           # favicon 
                           (r'^favicon\.ico', 'django.views.generic.simple.redirect_to', {'url': '/site_static/images/favicon.png'}),

                           # static files
                           # TODO
                           #      - move outside of django
                           (r'^static/(?P<path>.*)$', 'django.views.static.serve',
                            {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),

                           (r'^site_static/(?P<path>.*)$', 'django.views.static.serve',
                            {'document_root': settings.SITE_STATIC_ROOT, 'show_indexes': True}),

                           (r'^data/(?P<path>.*)$', 'django.views.static.serve',
                            {'document_root': settings.DATA_ROOT, 'show_indexes': True}),

                           
                           # debug
                           (r'^debug/redis/$', 'booki.portal.views.debug_redis'),                       
                           
                           # front page listing views
                           url(r'list-groups/', 'booki.portal.views.view_groups'),
                           url(r'list-books/', 'booki.portal.views.view_books'),
                           url(r'list-people/', 'booki.portal.views.view_people'),

                           # json booklist for objavi
                           url(r'^list-books.json$', 'booki.editor.views.view_books_json'),

                           # list of books by ID
                           url(r'^list-books-by-id/(?P<scheme>[\w. -]+).json?$', 'booki.portal.views.view_books_by_id'),
                           
                           # user accounts                     
                           url(r'^accounts/', include('booki.account.urls')),                    

                           # feeds
                           url(r'^feeds/rss/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedRSS()),
                           url(r'^feeds/atom/book/(?P<bookid>[\w\s\_\.\-\d]+)/$', feeds.BookFeedAtom()),
                           url(r'^feeds/rss/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedRSS()),
                           url(r'^feeds/atom/chapter/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<chapterid>[\w\s\_\.\-\d]+)/$', feeds.ChapterFeedAtom()),
                           url(r'^feeds/rss/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedRSS()),
                           url(r'^feeds/atom/user/(?P<userid>[\w\s\_\.\-\d]+)/$', feeds.UserFeedAtom()),

                           # groups
                           url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/add_book/$', 'booki.portal.views.add_book'),                    
                           url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/remove_book/$', 'booki.portal.views.remove_book'),                    
                           
                           url(r'^groups/(?P<groupid>[\w\s\_\.\-]+)/$', 'booki.portal.views.view_group', name="view_group"),                    
                           
                           # misc
                           url(r'^_utils/profilethumb/(?P<profileid>[\w\d\_\.\-]+)/thumbnail.jpg$', 'booki.account.views.view_profilethumbnail', name='view_profilethumbnail'),                             url(r'^_utils/profileinfo/(?P<profileid>[\w\d\_\.\-]+)/$', 'booki.utils.pages.profileinfo', name='view_profileinfo'),                      
                           url(r'^_utils/attachmentinfo/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<version>[\w\d\.\-]+)/(?P<attachment>.*)$', 'booki.utils.pages.attachmentinfo'),                      

                           (r'^robots.txt$', direct_to_template, {'template':'robots.txt', 'mimetype':'text/plain'}),

                           # export
                           url(r'^export/(?P<bookid>[\w\s\_\.\-]+)/export/{0,1}$',  'booki.editor.views.export', name='export_booki'), 
                           
                           # sputnik dispatcher                       
                           url(r'^_sputnik/$', 'sputnik.views.dispatcher', {
                              "map": (  
                                 (r'^/booki/$',                                       'booki.channels.main'),
                                 (r'^/booki/book/(?P<bookid>\d+)/(?P<version>[\w\d\.\-]+)/$', 'booki.channels.editor'),
                                 (r'^/booki/profile/(?P<profileid>.+)/$',             'booki.channels.profile'),
                                 (r'^/booki/group/(?P<groupid>.+)/$',                 'booki.channels.group'),
                                 (r'^/chat/(?P<bookid>\d+)/$',                        'booki.channels.chat')
                                      )
                              }),                     

                           url(r'^messaging/', include('booki.messaging.urls')),

                           # reader
                           url(r'^(?P<bookid>[\w\s\_\.\-\d]+)/', include('booki.editor.urls'))
                           )
