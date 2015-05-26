import datetime

from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _

from booki.editor.models import BookVersion


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
