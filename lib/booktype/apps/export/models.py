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
import os
import shutil
import logging

from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.conf import settings

from booki.editor.models import BookVersion, Book

logger = logging.getLogger('booktype')


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
    filename = models.CharField(_('File name'), max_length=300, blank=True, null=True)

    class Meta:
        verbose_name = _('Export File')
        verbose_name_plural = _('Export Files')

def has_subdir(dirpath):
    for subname in os.listdir(dirpath):
        subpath = os.path.join(dirpath, subname)
        if os.path.isdir(subpath):
            return True
    return False

@receiver(post_delete, sender=ExportFile)
def _exportfile_delete(sender, instance, **kwargs):
    try:
        relative_export_file = instance.filename.lstrip('/')
        export_file = os.path.join(settings.BOOKTYPE_ROOT, relative_export_file)
        export_type_dir = os.path.dirname(export_file)
        export_main_dir = os.path.dirname(export_type_dir)
        shutil.rmtree(export_type_dir)
        if not has_subdir(export_main_dir):
            shutil.rmtree(export_main_dir)
    except Exception as e:
        logger.error('Error deleting export files: {}'.format(e))


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
