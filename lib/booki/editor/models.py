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
import os
import time
import datetime

from django.db import models
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _

import booki.editor.signals


# License

class License(models.Model):
    name = models.CharField(_('name'), max_length=100, blank=False)
    abbrevation = models.CharField(_('abbrevation'), max_length=30)
    url = models.URLField(_('url'), blank=True, null=True)

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

    @models.permalink
    def get_absolute_url(self):
        return ('portal:group', [self.url_name])

    try:
        GROUP_IMAGE_UPLOAD_DIR = settings.GROUP_IMAGE_UPLOAD_DIR
    except AttributeError:
        GROUP_IMAGE_UPLOAD_DIR = 'group_images/'

    def get_big_group_image(self):
        group_image_path = '%s/%s' % (settings.MEDIA_ROOT, self.GROUP_IMAGE_UPLOAD_DIR)
        if(os.path.isfile(('%s/%s.jpg') % (group_image_path, self.pk)) is False):
            group_image = '%score/img/groups-big.png' % settings.STATIC_URL
        else:
            group_image = '%s%s%s.jpg' % (settings.MEDIA_URL, self.GROUP_IMAGE_UPLOAD_DIR, self.pk)

        return group_image

    def get_group_image(self):
        group_image_path = '%s/%s' % (settings.MEDIA_ROOT, self.GROUP_IMAGE_UPLOAD_DIR)
        if(os.path.isfile(('%s/%s_small.jpg') % (group_image_path, self.pk)) is False):
            group_image = '%score/img/groups.png' % settings.STATIC_URL
        else:
            group_image = '%s%s%s_small.jpg' % (settings.MEDIA_URL, self.GROUP_IMAGE_UPLOAD_DIR, self.pk)

        return group_image

    def remove_group_images(self):
        group_image_path = '%s/%s' % (settings.MEDIA_ROOT, self.GROUP_IMAGE_UPLOAD_DIR)
        
        group_images = []
        group_images.append('{0}/{1}_small.jpg'.format(group_image_path, self.pk))
        group_images.append('{0}/{1}.jpg'.format(group_image_path, self.pk))

        for image_path in group_images:
            try:
                os.remove(image_path)
            except Exception as err:
                # TODO: should log this error
                print err

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Booktype group')
        verbose_name_plural = _('Booktype groups')

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
    license = models.ForeignKey(License, null=True, blank=True, verbose_name=_("license"))

    created = models.DateTimeField(_('created'), auto_now=False, default=datetime.datetime.now)
    published = models.DateTimeField(_('published'), null=True)

    hidden = models.BooleanField(_('hidden'))
    permission = models.SmallIntegerField(_('permission'), null=False, default = 0) 

    description = models.TextField(_('description'), null=False, default='')
    cover = models.ImageField(_('cover'), upload_to=settings.COVER_IMAGE_UPLOAD_DIR, null=True)

    def get_version(self, version=None):
        """
        Returns object of type C{BookiVersion}. If version is None it returns latest version.

        @type version: C{string}
        @param version: Book version.

        @rtype version: C{booki.editor.models.BookVersion}
        @return: BookVersion object.
        """

        from booki.editor import models as emodels

        if not version:
            return self.version
        else:
            if version.find('.') == -1:
                try:
                    return emodels.BookVersion.objects.get(book=self, name=version)
                except emodels.BookVersion.DoesNotExist:
                    return None
                except emodels.BookVersion.MultipleObjectsReturned:
                    # would it be better to return first item in this situation?
                    return None
            else:
                v = version.split('.')
                if len(v) != 2: return None

                try:
                    book_ver = emodels.BookVersion.objects.get(book=self, major = int(v[0]), minor = int(v[1]))
                except ValueError:
                    return None
                except emodels.BookVersion.DoesNotExist:
                    return None
                except emodels.BookVersion.MultipleObjectsReturned:
                    # would it be better to return first item in this situation?
                    return None                

        return book_ver

    def get_versions(self):
        """
        @rtype: C{list}
        @return: List of all BookVersions for this Book.
        """

        from booki.editor import models as emodels
        return emodels.BookVersion.objects.filter(book=self)

    def set_cover(self, fileName):
        from booktype.utils.book import set_book_cover

        set_book_cover(self, fileName)

    def get_absolute_url(self):
        return '%s/%s/' % (settings.BOOKI_URL, self.url_title)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

    # DEPRECATED API NAMES
    getVersion = get_version
    getVersions = get_versions
    setCover = set_cover


# BookHistory


HISTORY_CHOICES = {
    'unknown': 0,
    
    'chapter_create': 1,
    'chapter_save': 2,
    'chapter_rename': 3,
    'chapter_reorder': 4,
    'chapter_split': 5,
    'chapter_clone': 15,
    'chapter_delete': 19,

    'section_create': 6,
    'section_rename': 7,
    'section_delete': 20,

    'book_create': 10,
    'minor_version': 11,
    'major_version': 12,

    'attachment_upload': 13,
    'attachment_delete': 14,

    'cover_upload': 16,
    'cover_delete': 17,
    'cover_update': 18
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

    
    def get_value(self):
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

    # DEPRECATED API NAMES
    getValue = get_value        


# Book Version

class BookVersion(models.Model):
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    major = models.IntegerField(_('major'))
    minor = models.IntegerField(_('minor'))
    name = models.CharField(_('name'), max_length=50, blank=True)
    description = models.CharField(_('description'), max_length=250, blank=True)

    created = models.DateTimeField(_('created'), auto_now=False, null=False, default=datetime.datetime.now)
    # add published

    def get_toc(self):
        return BookToc.objects.filter(version=self).order_by("-weight")

    def get_hold_chapters(self):
        return Chapter.objects.raw('SELECT editor_chapter.* FROM editor_chapter LEFT OUTER JOIN editor_booktoc ON (editor_chapter.id=editor_booktoc.chapter_id)  WHERE editor_chapter.book_id=%s AND editor_chapter.version_id=%s AND editor_booktoc.chapter_id IS NULL', (self.book.id, self.id))

    def get_attachments(self):
        "Return all attachments for this version."
        return Attachment.objects.filter(version=self)

    def get_version(self):
        return '%d.%d' % (self.major, self.minor)

    def get_absolute_url(self):
        return '%s/%s/_v/%s/' % (settings.BOOKI_URL, self.book.url_title, self.get_version())
        
    def __unicode__(self):
        return '%d.%d (%s)' % (self.major, self.minor, self.name)

    # DEPRECATED API NAMES
    getTOC = get_toc        
    getHoldChapters = get_hold_chapters
    getAttachments = get_attachments
    getVersion = get_version


# Chapter

class Chapter(models.Model):
    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("version"))
    # don't need book
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))

    url_title = models.CharField(_('url title'), max_length=2500)
    title = models.CharField(_('title'), max_length=2500)
    status = models.ForeignKey(BookStatus, null=False, verbose_name=_("status")) # this will probably change
    created = models.DateTimeField(_('created'), null=False, auto_now=False, default=datetime.datetime.now)
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

    def previous(self):
        lower = ChapterHistory.objects.filter(
                    chapter=self.chapter, revision__lt=self.revision
                ).order_by('-revision')
        if lower.count() > 0:
            return lower[0].revision
        return None

    def next(self):
        higher = ChapterHistory.objects.filter(chapter=self.chapter, revision__gt=self.revision)
        if higher.count() > 0:
            return higher[0].revision
        return None

# Attachment

def uploadAttachmentTo(att, filename):
    return '%s/books/%s/%s/%s' % (settings.DATA_ROOT, att.book.url_title, att.version.get_version(), filename)

def getAttachmentUrl(att, filename):
    return '%sbooks/%s/%s/%s' % (settings.DATA_URL, att.book.url_title, att.version.get_version(), filename)
#    return '%s%s/%s/%s' % (settings.MEDIA_ROOT, att.book.url_title, att.version.get_version(), filename)



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
    created = models.DateTimeField(_('created'), null=False, auto_now=False, default=datetime.datetime.now)

    def get_name(self):
        name = self.attachment.name
        return name[name.rindex('/')+1:]

    def delete(self):
        self.attachment.delete(save=False)

        super(Attachment, self).delete()

    def __unicode__(self):
        return self.attachment.name


    def thumbnail(self, size=(100, 100)):
        '''returns URL for a thumbnail with the specified size'''
        from booki.utils.misc import createThumbnail
        filename, ext = os.path.splitext(os.path.basename(self.attachment.url))
        w, h = size
        filename = '%s_%s_%s_%sx%s%s' % (filename, self.pk,
                                         time.mktime(self.created.timetuple()),
                                         w, h, ext)
        im_path = uploadAttachmentTo(self, filename)
        im_url =  getAttachmentUrl(self, filename)
        if not os.path.exists(im_path):
            im = createThumbnail(self.attachment, size=size)
            im.save(im_path, 'JPEG')
        return im_url

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    # DEPRECATED API NAMES
    getName = get_name        

    
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
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_("parent"))
    name = models.CharField(_('name'), max_length=2500, blank=True)
    chapter = models.ForeignKey(Chapter, null=True, blank=True, verbose_name=_("chapter"))
    weight = models.IntegerField(_('weight'))
    typeof = models.SmallIntegerField(_('typeof'), choices=TYPEOF_CHOICES)

    def is_section(self):
        return self.typeof == 0

    def is_chapter(self):
        return self.typeof == 1

    def has_children(self):
        return (self.booktoc_set.count() > 0)

    def url_title(self):
        if self.is_chapter():
            return self.chapter.url_title
        return None

    def __unicode__(self):
        return unicode(self.weight)

    class Meta:
        verbose_name = _('Book TOC')
        verbose_name_plural = _('Book TOCs')

    # DEPRECATED API NAMES
    isSection = is_section
    isChapter = is_chapter


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
        unique_together = ('book', 'user', 'wizz_type')


def uploadCoverTo(att, filename):
    extension = os.path.splitext(filename)[-1].lower()
    return '%s/book_covers/%s%s' % (settings.DATA_ROOT, att.id, extension)


class BookCover(models.Model):
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))

    cid = models.CharField('cid', max_length=40, null=False, default='', unique=True)

    attachment = models.FileField(_('filename'), upload_to=uploadCoverTo, max_length=2500)
    filename = models.CharField('file name', max_length=250, unique=False, default='')
    title = models.CharField(_('Cover title'), max_length=250, blank=False, unique=False)

    width = models.IntegerField(_('Width'), blank=True)
    height = models.IntegerField(_('Height'), blank=True)
    unit = models.CharField(_('Unit'), max_length=20, blank=True)
    booksize = models.CharField(_('Booksize'), max_length=30, blank=True)

    is_book = models.BooleanField(_('Book cover'), default=False)
    is_ebook = models.BooleanField(_('E-book cover'), default=False)
    is_pdf = models.BooleanField(_('PDF cover'), default=False)

    cover_type = models.CharField(_('Cover type'), max_length=20, blank=True)

    creator = models.CharField(_('Cover'), max_length=40, blank=True)
    license = models.ForeignKey(License,null=True, verbose_name=_("license"))

    notes = models.TextField(_('notes'))

    approved = models.BooleanField(_('Approved'), blank=False, default=False)

    created = models.DateTimeField(_('created'), auto_now=False, null=False)

    def delete(self):
        self.attachment.delete(save=False)

        super(BookCover, self).delete()

    def __unicode__(self):
        return '%s' % (self.id, )

