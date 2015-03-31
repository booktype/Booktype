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

from django.conf.urls import patterns, url

from .views import CreateBookView, UserSettingsPage, DashboardPageView
from .views import (ForgotPasswordView, ForgotPasswordEnterView, SignInView, SignOutView,
                    SendInviteView)

urlpatterns = patterns(
    '',
    url(r'^signin/$', SignInView.as_view(), name='signin'),
    url(r'^signout/$', SignOutView.as_view(), name='signout'),
    url(r'^forgot_password/$', ForgotPasswordView.as_view(), name='forgotpassword'),
    url(r'^forgot_password/enter/$', ForgotPasswordEnterView.as_view(), name='forgotpasswordenter'),
    url(r'^invite/$', SendInviteView.as_view(), name='invite'),

    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/$', DashboardPageView.as_view(), name='view_profile'),
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/_create_book/$', CreateBookView.as_view(), name='create_book'),
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/_settings/$', UserSettingsPage.as_view(), name='user_settings'),
)
