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

from django.conf.urls import url
from . import views as cc_views


urlpatterns = [
    url(r'^$', cc_views.ControlCenterView.as_view(), name='frontpage'),
    url(r'^settings/$', cc_views.ControlCenterSettings.as_view(), name='settings'),

    url(r'^statistics/$', cc_views.StatisticsView.as_view(), name='statistics'),
    url(r'^people/$', cc_views.PeopleListView.as_view(), name='people_list'),
    url(r'^people/(?P<username>[\w\d\@\.\+\-\_\s]+)/info/$',
        cc_views.PersonInfoView.as_view(), name='person_info'),
    url(r'^people/(?P<username>[\w\d\@\.\+\-\_\s]+)/edit/$',
        cc_views.EditPersonInfo.as_view(), name='person_edit'),
    url(r'^people/(?P<username>[\w\d\@\.\+\-\_\s]+)/password/$',
        cc_views.PasswordChangeView.as_view(), name='password_change'),

    url(r'^books/(?P<bookid>[\w\s\_\.\-\d]+)/rename/$',
        cc_views.BookRenameView.as_view(), name='rename_book'),
    url(r'^groups/(?P<groupid>[\w\s\_\.\-\d]+)/delete/$',
        cc_views.DeleteGroupView.as_view(), name='delete_group'),
    url(r'^licenses/(?P<pk>\d+)/edit/$',
        cc_views.LicenseEditView.as_view(), name="license_edit"),
    url(r'^licenses/(?P<pk>\d+)/delete/$',
        cc_views.DeleteLicenseView.as_view(), name="delete_license"),

    url(r'^roles/(?P<pk>\d+)/edit/$',
        cc_views.RoleEditView.as_view(), name="role_edit"),
    url(r'^roles/(?P<pk>\d+)/delete/$',
        cc_views.DeleteRoleView.as_view(), name="delete_role"),

    url(r'^book-skeleton/(?P<pk>\d+)/edit/$',
        cc_views.BookSkeletonEditView.as_view(), name="book_skeleton_edit"),
    url(r'^book-skeleton/(?P<pk>\d+)/delete/$',
        cc_views.DeleteBookSkeletonView.as_view(), name="delete_book_skeleton"),
]
