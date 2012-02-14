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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import models as auth_models

import booki.editor.signals

from django.conf import settings

# License

class License(models.Model):
    name = models.CharField(_('name'), max_length=100, blank=False)
    abbrevation = models.CharField(_('abbrevation'), max_length=30)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('License')
        verbose_name_plural = _('Licenses')

# Language

class Language(models.Model):
    name = models.CharField(_('name'), max_length=50, blank=False)
    abbrevation = models.CharField(_('abbrevation'), max_length=10, blank=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')

# Project

STATUS_CHOICES = (
    (0, _('published')),
    (1, _('not published')),
    (2, _('not translated'))
)


# Book Status

class BookStatus(models.Model):
    book = models.ForeignKey('Book', verbose_name=_("book"))
    name = models.CharField(_('name'), max_length=30, blank=False)
    weight = models.SmallIntegerField(_('weight'))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Book status')
        verbose_name_plural = _('Book status')

# Book Notes
# free form shared notes for writers of the book
#
class BookNotes(models.Model):
    book = models.ForeignKey('Book', verbose_name=_("book"))
    notes = models.TextField(_('notes'))

    def __unicode__(self):
        return "Notes for " + self.book.title

    class Meta:
        verbose_name = _('Book note')
        verbose_name_plural = _('Book notes')

# BookiGroup

class BookiGroup(models.Model):
    name = models.CharField(_('name'), max_length=300, blank=False)
    url_name = models.CharField(_('url name'), max_length=300, blank=False) #, primary_key=True)
    description = models.TextField(_('description'))

    owner = models.ForeignKey(auth_models.User, verbose_name=_('owner'))

#    books = models.ManyToManyField(Book, blank=True)
    members = models.ManyToManyField(auth_models.User, related_name="members", blank=True, verbose_name=_("members"))

    created = models.DateTimeField(_('created'), auto_now=False, null=True)

    def get_absolute_url(self):
        return '%s/groups/%s/' % (settings.BOOKI_URL, self.url_name)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Booki group')
        verbose_name_plural = _('Booki groups')

# Book

class Book(models.Model):
    url_title = models.CharField(_('url title'), max_length=2500, blank=False, unique=True) # can it be blank?
    title = models.CharField(_('title'), max_length=2500, blank=False)
    status = models.ForeignKey('BookStatus', null=True, related_name="status", verbose_name=_("status"))
    language = models.ForeignKey(Language, null=True, verbose_name=_("language")) # can it be blank?

    # this i need
    version = models.ForeignKey('BookVersion', null=True, related_name="version", verbose_name=_("version"))

    group = models.ForeignKey(BookiGroup, null=True, verbose_name=_("group"))

    owner = models.ForeignKey(auth_models.User, verbose_name=_("owner"))

    # or is this suppose to be per project
    # and null=False should be
    license = models.ForeignKey(License,null=True, verbose_name=_("license"))

    created = models.DateTimeField(_('created'), auto_now=True)
    published = models.DateTimeField(_('published'), null=True)

    hidden = models.BooleanField(_('hidden'))
    permission = models.SmallIntegerField(_('permission'), null=False, default = 0) 

    description = models.TextField(_('description'), null=False, default='')
    cover = models.ImageField(_('cover'), upload_to=settings.COVER_IMAGE_UPLOAD_DIR, null=True)

    def get_absolute_url(self):
        return '%s/%s/' % (settings.BOOKI_URL, self.url_title)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

# BookHistory


HISTORY_CHOICES = {'unknown': 0,

                   'chapter_create': 1,
                   'chapter_save': 2,
                   'chapter_rename': 3,
                   'chapter_reorder': 4,
                   'chapter_split': 5,

                   'section_create': 6,

                   'book_create': 10,
                   'minor_version': 11,
                   'major_version': 12,

                   'attachment_upload': 13,
                   'attachment_delete': 14
}

class BookHistory(models.Model):
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    # this should probably be null=False
    version = models.ForeignKey('BookVersion', null=True, verbose_name=_("version"))
    chapter = models.ForeignKey('Chapter', null=True, verbose_name=_("chapter"))
    chapter_history = models.ForeignKey('ChapterHistory', null=True, verbose_name=_("chapter history"))
    modified = models.DateTimeField(_('modified'), auto_now=True)
    args = models.CharField(_('args'), max_length=2500, blank=False)
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    kind = models.SmallIntegerField(_('kind'), default=0)

    def __unicode__(self):
        return self.args


# Info

INFO_CHOICES = (
    (0, 'string'),
    (1, 'integer'),
    (2, 'text'),
    (3, 'date')
)


# msu add version here
class Info(models.Model):
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))

    name = models.CharField(_('name'), max_length=2500, db_index=True)
    kind = models.SmallIntegerField(_('kind'), choices=INFO_CHOICES)

    value_string = models.CharField(_('value string'), max_length=2500, null=True)
    value_integer = models.IntegerField(_('value integer'), null=True)
    value_text = models.TextField(_('value text'), null=True)
    value_date = models.DateTimeField(_('value date'), auto_now=False, null=True)

    
    def getValue(self):
        if self.kind == 0:
            return self.value_string
        if self.kind == 1:
            return self.value_integer
        if self.kind == 2:
            return self.value_text
        if self.kind == 3:
            return self.value_date

        return None
        

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Metadata')
        verbose_name_plural = _('Metadata')


# Book Version

class BookVersion(models.Model):
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    major = models.IntegerField(_('major'))
    minor = models.IntegerField(_('minor'))
    name = models.CharField(_('name'), max_length=50, blank=True)
    description = models.CharField(_('description'), max_length=250, blank=True)

    created = models.DateTimeField(_('created'), auto_now=True, null=False)
    # add published

    def getTOC(self):
        return BookToc.objects.filter(version=self).order_by("-weight")

    def getHoldChapters(self):
        return Chapter.objects.raw('SELECT editor_chapter.* FROM editor_chapter LEFT OUTER JOIN editor_booktoc ON (editor_chapter.id=editor_booktoc.chapter_id)  WHERE editor_chapter.book_id=%s AND editor_chapter.version_id=%s AND editor_booktoc.chapter_id IS NULL', (self.book.id, self.id))


    def getAttachments(self):
        "Return all attachments for this version."
        return Attachment.objects.filter(version=self)

    def getVersion(self):
        return '%d.%d' % (self.major, self.minor)

    def get_absolute_url(self):
        return '%s/%s/_v/%s/' % (settings.BOOKI_URL, self.url_title, self.getVersion())
        
    def __unicode__(self):
        return '%d.%d (%s)' % (self.major, self.minor, self.name)
        

# Chapter

class Chapter(models.Model):
    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("version"))
    # don't need book
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))

    url_title = models.CharField(_('url title'), max_length=2500)
    title = models.CharField(_('title'), max_length=2500)
    status = models.ForeignKey(BookStatus, null=False, verbose_name=_("status")) # this will probably change
    created = models.DateTimeField(_('created'), null=False, auto_now=True)
    modified = models.DateTimeField(_('modified'), null=True, auto_now=True)
    #
    revision = models.IntegerField(_('revision'), default=1)
#    comment = models.CharField(_('comment'), max_length=2500, blank=True)


    # missing licence here
    content = models.TextField(_('content'))

    def get_absolute_url(self):
        return '%s/%s/%s/' % (settings.BOOKI_URL, self.book.url_title, self.url_title)


    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')

# ChapterHistory

class ChapterHistory(models.Model):
    chapter = models.ForeignKey(Chapter, null=False, verbose_name=_("chapter"))
    content = models.TextField()
    modified = models.DateTimeField(_('modified'), null=False, auto_now=True)
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    revision = models.IntegerField(_('revision'), default=1)
    comment = models.CharField(_('comment'), max_length=2500, blank=True)

    def __unicode__(self):
        return self.comment

    class Meta:
        verbose_name = _('Chapter history')
        verbose_name_plural = ('Chapters history')


# Attachment

def uploadAttachmentTo(att, filename):
    return '%s/books/%s/%s/%s' % (settings.DATA_ROOT, att.book.url_title, att.version.getVersion(), filename)
#    return '%s%s/%s/%s' % (settings.MEDIA_ROOT, att.book.url_title, att.version.getVersion(), filename)



class AttachmentFile(models.FileField):
    def get_directory_name(self):
        # relative path
        name = super(models.FileField, self).get_directory_name()
        return name

# TODO
# should add version

class Attachment(models.Model):
    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("version"))
    # don't really need book anymore
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))

    attachment = models.FileField(_('filename'), upload_to=uploadAttachmentTo, max_length=2500)

    status = models.ForeignKey(BookStatus, null=False, verbose_name=_("status"))
    created = models.DateTimeField(_('created'), null=False, auto_now=True)

    def getName(self):
        name = self.attachment.name
        return name[name.rindex('/')+1:]

    def __unicode__(self):
        return self.attachment.name

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    
# Book Toc

TYPEOF_CHOICES = (
    (0, _('section name')),
    (1, _('chapter name')),
    (2, _('line'))
)


class BookToc(models.Model):
    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("version"))
    # book should be removed
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    name = models.CharField(_('name'), max_length=2500, blank=True)
    chapter = models.ForeignKey(Chapter, null=True, blank=True, verbose_name=_("chapter"))
    weight = models.IntegerField(_('weight'))
    typeof = models.SmallIntegerField(_('typeof'), choices=TYPEOF_CHOICES)

    def isSection(self):
        return self.typeof == 0

    def isChapter(self):
        return self.typeof == 1


    def __unicode__(self):
        return unicode(self.weight)


    class Meta:
        verbose_name = _('Book TOC')
        verbose_name_plural = _('Book TOCs')



class BookiPermission(models.Model):
    """
    - permission 
        0 - unknown
        1 - admin
    """

    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    group = models.ForeignKey(BookiGroup, null=True, verbose_name=_("group"))
    permission = models.SmallIntegerField(_('permission'))


    def __unicode__(self):
        return '%s %s ' % (self.user.username, self.permission)


class AttributionExclude(models.Model):
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))

    def __unicode__(self):
        return '%s' % (self.user.username, )

    class Meta:
        verbose_name = _('Attribution Exclude')
        verbose_name_plural = _('Attribution Exclude')


class PublishWizzard(models.Model):
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    wizz_type = models.CharField(_('wizzard type'), max_length=20, blank=False)
    wizz_options =  models.TextField(_('wizzard options'), default='', null=False)

    def __unicode__(self):
        return '%s' % (self.book.url_title, )

    class Meta:
        verbose_name = _('Publish Wizzard')
        verbose_name_plural = _('Publish Wizzard')

    
