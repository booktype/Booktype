# This file is part of Booktype.
# Copyright (c) 2012
# Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import datetime

from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _

from booki.editor.models import BookVersion, Book


class BookExport(models.Model):
    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("export"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"), null=True)
    name = models.CharField(_('Name'), max_length=100, blank=False)
    task_id = models.CharField(_('Task ID'), max_length=64, null=False, unique=True, db_index=True)
    created = models.DateTimeField(_('Created'), auto_now=False, default=datetime.datetime.now)
    published = models.DateTimeField(_('Published'), auto_now=False, null=True)
    status = models.SmallIntegerField(_('Status'), default=0, null=False)

    class Meta:
        verbose_name = _('Book Export')
        verbose_name_plural = _('Book Exports')

    @property
    def book_title(self):
        return self.version.book.title


class ExportFile(models.Model):
    export = models.ForeignKey(BookExport, null=False, verbose_name=_("export"))
    typeof = models.CharField(_('Export type'), max_length=20, blank=False, null=False)
    filesize = models.IntegerField(_('File size'), default=0, null=True)
    pages = models.IntegerField(_('Number of pages'), default=0, null=True)
    status = models.SmallIntegerField(_('Status'), default=0, null=False)
    description = models.TextField(_('Description'))
    filename = models.CharField(_('File name'), max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = _('Export File')
        verbose_name_plural = _('Export Files')


class ExportComment(models.Model):
    export = models.ForeignKey(BookExport, null=False, verbose_name=_("version"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    created = models.DateTimeField(_('Created'), auto_now=False, default=datetime.datetime.now)
    content = models.TextField(_('Content'), default='')

    class Meta:
        verbose_name = _('Export Comment')
        verbose_name_plural = _('Export Comments')


class ExportSettings(models.Model):
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    typeof = models.CharField(_('Export type'), max_length=20, blank=False, null=False)
    data = models.TextField(_('Data'), default='{}', null=False)
    created = models.DateTimeField(_('Created'), auto_now=False, default=datetime.datetime.now)

    class Meta:
        verbose_name = _('Export Settings')
        verbose_name_plural = _('Export Settings')
