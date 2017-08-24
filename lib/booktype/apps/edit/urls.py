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

from .views import (
    EditBookPage, BookHistoryPage, RevisionPage,
    ChapterHistoryPage, CompareChapterRevisions, BookSettingsView,
    DownloadBookHistory, InviteCodes
)
from .views import upload_attachment, upload_cover, cover
from booktype.apps.core.views import staticattachment

urlpatterns = [
    url(r'^_upload/$', upload_attachment, name='upload_attachment'),
    url(r'^_upload_cover/$', upload_cover, name='upload_cover'),
    url(r'^_cover/(?P<cid>[\w\s\_\d\.\-]+)/(?P<fname>.*)$', cover, name='view_cover'),
    url(r'^_edit/static/(?P<attachment>.*)$', staticattachment),

    url(r'^_edit/$', EditBookPage.as_view(), name='editor'),
    url(r'^_history/$', BookHistoryPage.as_view(), name='history'),
    url(r'^_history/download/$', DownloadBookHistory.as_view(), name='download_history'),
    url(r'^_history/(?P<chapter>[\w\s\_\.\-]+)/download/$',
        DownloadBookHistory.as_view(), name='download_chapter_history'),

    url(r'^_history/(?P<chapter>[\w\s\_\.\-]+)/$',
        ChapterHistoryPage.as_view(), name='chapter_history'),

    url(r'^_history/(?P<chapter>[\w\s\_\.\-]+)/compare-revs/(?P<rev_one>\d+)/(?P<rev_two>\d+)/$',
        CompareChapterRevisions.as_view(), name='revisions_compare'),

    url(r'^_history/(?P<chapter>[\w\s\_\.\-]+)/rev/(?P<revid>\d+)/$',
        RevisionPage.as_view(), name='chapter_revision'),

    url(r'^_history/(?P<chapter>[\w\s\_\.\-]+)/rev/(?P<revid>\d+)/static/(?P<attachment>.*)$',
        staticattachment),

    url(r'^_settings/$', BookSettingsView.as_view(), name='settings'),

    url(r'^_invite_codes/$', InviteCodes.as_view(), name='invite_codes'),
]
