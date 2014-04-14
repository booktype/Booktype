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
from django.conf import settings

# This is dispatcher for Sputnik connections.

SPUTNIK_DISPATCHER = ((r'^/booki/$',                                       'booki.channels.main'),
                      (r'^/booki/profile/(?P<profileid>.+)/$',             'booki.channels.profile'),
                      (r'^/chat/(?P<bookid>\d+)/$',                        'booki.channels.chat'),
                      (r'^/booktype/book/(?P<bookid>\d+)/(?P<version>[\w\d\.\-.]+)/$', 'booktype.apps.edit.channel')
                      )

urlpatterns = patterns('',
                   # front page                       
                   url(r'', include('booktype.apps.portal.urls', namespace="portal")),

                   # booktype control center
                   # TODO: Add namespace
                   url(r'^_control/', include('booktypecontrol.urls')),

                   # convert
                   # TODO: Add namespace
                   url(r'^_convert/', include('booktype.apps.convert.urls')),

                   (r'^data/(?P<path>.*)$', 'django.views.static.serve',
                    {'document_root': settings.DATA_ROOT, 'show_indexes': True}),
                                      
                   # user accounts                     
                   # TODO; replace with new app
                   url(r'^accounts/', include('booki.account.urls')),                    
                   
                   # misc
                   # TODO: replace with new apps
                   url(r'^_utils/profilethumb/(?P<profileid>[\w\d\_\.\-]+)/thumbnail.jpg$', 'booki.account.views.view_profilethumbnail', name='view_profilethumbnail'),                             
                   url(r'^_utils/profileinfo/(?P<profileid>[\w\d\_\.\-]+)/$', 'booki.utils.pages.profileinfo', name='view_profileinfo'),                      
                   url(r'^_utils/attachmentinfo/(?P<bookid>[\w\s\_\.\-\d]+)/(?P<version>[\w\d\.\-]+)/(?P<attachment>.*)$', 'booki.utils.pages.attachmentinfo'),                      

                   # export
                   #url(r'^export/(?P<bookid>[\w\s\_\.\-]+)/export/{0,1}$',  'booki.editor.views.export', name='export_booki'), 
                   
                   # sputnik dispatcher                       
                   url(r'^_sputnik/$', 'sputnik.views.dispatcher', {"map": SPUTNIK_DISPATCHER}, name='sputnik_dispatcher'),

                   # messaging application
                   # TODO: remove this application
                   url(r'^messaging/', include('booki.messaging.urls')),

                   # importer application
                   # TODO: Add namespace
                   url(r'^importer/', include('booktype.apps.importer.urls'))                   
                   )

urlpatterns += patterns('',
                        # export
                        # TODO; Add namespace
                        url(r'^(?P<bookid>[\w\s\_\.\-\d]+)/', include('booktype.apps.loadsave.urls')),

                        # new editor
                        # TODO: Add namespace
                        url(r'^(?P<bookid>[\w\s\_\.\-\d]+)/', include('booktype.apps.edit.urls')),

                        # editor
                        url(r'^(?P<bookid>[\w\s\_\.\-\d]+)/', include('booki.editor.urls')),

                        # reader
                        # TODO: replace with new app
                        # - must be at the end
                        url(r'^(?P<bookid>[\w\s\_\.\-\d]+)/', include('booki.reader.urls')),

                        # new booktype reader app
                        url(r'^(?P<bookid>[\w\s\_\.\-\d]+)/reader/', include('booktype.apps.reader.urls', namespace='reader')),
              )
