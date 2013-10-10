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

from django.contrib.auth.decorators import login_required
from django.conf.urls import patterns, url, include

#from .views import ImporterView

urlpatterns = patterns('',                      
#                      url(r'^$', login_required(ImporterView.as_view()), name='importer'),                       
					   url(r'^$', 'booktype.apps.importer.views.frontpage', name='importer')
 #                     url(r'^$', ImporterView.as_view(), name='importer'),                       

                      )
