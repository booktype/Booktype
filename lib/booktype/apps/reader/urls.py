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

from django.conf.urls import patterns, url, include

from .views import InfoPageView, DeleteBookView, EditBookInfoView

urlpatterns = patterns('',
   url(r'^_info/$', InfoPageView.as_view(), name='infopage'),
   url(r'^_info/edit/$', EditBookInfoView.as_view(), name='edit_info_book'),
   url(r'^_info/delete/$', DeleteBookView.as_view(), name='delete_book'),
)