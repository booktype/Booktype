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

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'booktypecontrol.views.frontpage', name='control_frontpage'),

    url(r'^people/$', 'booktypecontrol.views.people', name='control_people'),
    url(r'^people/_add/$', 'booktypecontrol.views.add_person', name='control_add_person'),
    url(r'^people/(?P<username>[\w\d\@\.\+\-\_\s]+)/$', 'booktypecontrol.views.profile', name='control_profile'),
    url(r'^people/(?P<username>[\w\d\@\.\+\-\_\s]+)/_edit/$', 'booktypecontrol.views.edit_profile', name='control_edit_profile'),
    url(r'^people/(?P<username>[\w\d\@\.\+\-\_\s]+)/_password/$', 'booktypecontrol.views.edit_password', name='control_password'),

    url(r'^books/$', 'booktypecontrol.views.books', name='control_books'),
    url(r'^books/_add/$', 'booktypecontrol.views.add_book', name='control_add_book'),
    url(r'^books/(?P<bookid>[\w\s\_\.\-\d]+)/_edit/$', 'booktypecontrol.views.edit_book', name='control_edit_book'),
    url(r'^books/(?P<bookid>[\w\s\_\.\-\d]+)/_rename/$', 'booktypecontrol.views.rename_book', name='control_rename_book'),
    url(r'^books/(?P<bookid>[\w\s\_\.\-\d]+)/$', 'booktypecontrol.views.view_book', name='control_book'),

    url(r'^settings/$', 'booktypecontrol.views.viewsettings', name='control_settings'),
    url(r'^settings/description/$', 'booktypecontrol.views.settings_description', name='control_settings_description'),
    url(r'^settings/book_create/$', 'booktypecontrol.views.settings_book_create', name='control_settings_book_create'),
    url(r'^settings/license/$', 'booktypecontrol.views.settings_license', name='control_settings_license'),
    url(r'^settings/license/(?P<licenseid>[\d]+)/$', 'booktypecontrol.views.settings_license_edit', name='control_settings_license_edit'),
    url(r'^settings/privacy/$', 'booktypecontrol.views.settings_privacy', name='control_settings_privacy'),

    url(r'^settings/publishing/$', 'booktypecontrol.views.settings_publishing', name='control_settings_publishing'),
    url(r'^settings/publishing_defaults/$', 'booktypecontrol.views.settings_publishing_defaults', name='control_settings_publishing_defaults'),

    url(r'^settings/appearance/$', 'booktypecontrol.views.settings_appearance', name='control_settings_appearance'),

    url(r'^settings/frontpage/$', 'booktypecontrol.views.settings_frontpage', name='control_settings_frontpage'),
)
