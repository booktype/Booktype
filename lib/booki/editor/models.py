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
import sputnik
import logging

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _

try:
    from PIL import Image
except ImportError:
    import Image

logger = logging.getLogger('booktype')


# License
class License(models.Model):
    name = models.CharField(_('name'), max_length=100, blank=False)
    abbrevation = models.CharField(_('abbreviation'), max_length=30)
    url = models.URLField(_('url'), blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('License')
        verbose_name_plural = _('Licenses')


# Language
class Language(models.Model):
    name = models.CharField(_('name'), max_length=50, blank=False)
    abbrevation = models.CharField(_('abbreviation'),
                                   max_length=10, blank=False)

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


class BookStatus(models.Model):
    book = models.ForeignKey('Book', verbose_name=_("book"))
    name = models.CharField(_('name'), max_length=30, blank=False)
    weight = models.SmallIntegerField(_('weight'))
    color = models.CharField(_('color'), max_length=30, default='', blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ['book', 'name']
        verbose_name = _('Book status')
        verbose_name_plural = _('Book status')


# free form shared notes for writers of the book
class BookNotes(models.Model):
    book = models.ForeignKey('Book', verbose_name=_("book"))
    notes = models.TextField(_('notes'))

    def __unicode__(self):
        return u"Notes for " + self.book.title

    class Meta:
        verbose_name = _('Book note')
        verbose_name_plural = _('Book notes')


class BookiGroup(models.Model):
    name = models.CharField(_('name'), max_length=300, blank=False)
    url_name = models.CharField(_('url name'), max_length=300, blank=False)
    description = models.TextField(_('description'))

    owner = models.ForeignKey(auth_models.User, verbose_name=_('owner'))
    members = models.ManyToManyField(auth_models.User, related_name="members",
                                     blank=True, verbose_name=_("members"))

    created = models.DateTimeField(_('created'), auto_now=False, null=True)

    @models.permalink
    def get_absolute_url(self):
        return ('portal:group', [self.url_name])

    try:
        GROUP_IMAGE_UPLOAD_DIR = settings.GROUP_IMAGE_UPLOAD_DIR
    except AttributeError:
        GROUP_IMAGE_UPLOAD_DIR = 'group_images/'

    def get_big_group_image(self):
        group_image_path = os.path.join(settings.MEDIA_ROOT, self.GROUP_IMAGE_UPLOAD_DIR)

        if not os.path.isfile('{}.jpg'.format(os.path.join(group_image_path, str(self.pk)))):
            return os.path.join(settings.STATIC_URL, 'core/img/groups-big.png')
        return '{}.jpg'.format(os.path.join(settings.MEDIA_URL, self.GROUP_IMAGE_UPLOAD_DIR, str(self.pk)))

    def get_group_image(self):
        group_image_path = os.path.join(settings.MEDIA_ROOT, self.GROUP_IMAGE_UPLOAD_DIR)

        if not os.path.isfile("{}_small.jpg".format(os.path.join(group_image_path, str(self.pk)))):
            return os.path.join(settings.STATIC_URL, 'core/img/groups.png')
        return '{}_small.jpg'.format(os.path.join(settings.MEDIA_URL, self.GROUP_IMAGE_UPLOAD_DIR, str(self.pk)))

    def remove_group_images(self):
        group_image_path = os.path.join(settings.MEDIA_ROOT, self.GROUP_IMAGE_UPLOAD_DIR)

        group_images = []
        group_images.append('{}_small.jpg'.format(os.path.join(group_image_path, str(self.pk))))
        group_images.append('{}.jpg'.format(os.path.join(group_image_path, str(self.pk))))

        for image_path in group_images:
            try:
                os.remove(image_path)
            except Exception as e:
                logger.exception(e)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Booktype group')
        verbose_name_plural = _('Booktype groups')

# METADATA namespace
DC = 'DC'  # Dublin Core
DCTERMS = 'DCTERMS'  # http://dublincore.org/documents/dcmi-terms/#H2
BKTERMS = 'BKTERMS'  # custom booktype metadata terms
ADD_META_TERMS = 'ADD_META_TERMS'  # custom booktype prefix for additional metadata

# I'm using a list instead of a dict because I want
# to mantain certain order on forms.MetadataForm fields
METADATA_FIELDS = [
    ('creator', _('Author(s)'), DC),

    ('title', _('Title'), DC),
    ('short_title', _('Short title'), BKTERMS),
    ('subtitle', _('Subtitle'), BKTERMS),

    ('publisher', _('Publisher'), DC),
    ('issued', _('Publication date'), DCTERMS),
    ('dateCopyrighted', _('Copyright date'), DCTERMS),
    ('rightsHolder', _('Copyright holder'), DCTERMS),

    # here below all the custom fields from booktype
    ('publisher_city', _('City of publication'), BKTERMS),
    ('publisher_country', _('Country of publication'), BKTERMS),
    ('short_description', _('Short description'), BKTERMS),
    ('long_description', _('Long description'), BKTERMS),

    ('ebook_isbn', _('Ebook ISBN'), BKTERMS),
    ('print_isbn', _('Print ISBN'), BKTERMS)
]


class Book(models.Model):
    url_title = models.CharField(_('url title'), max_length=2500, blank=False, unique=True)  # can it be blank?
    title = models.CharField(_('title'), max_length=2500, blank=False)
    status = models.ForeignKey('BookStatus', null=True, related_name="status", verbose_name=_("status"))
    language = models.ForeignKey(Language, null=True, verbose_name=_("language"))  # can it be blank?

    version = models.ForeignKey('BookVersion', null=True, related_name="version", verbose_name=_("version"))

    group = models.ForeignKey(BookiGroup, null=True, verbose_name=_("group"))

    owner = models.ForeignKey(auth_models.User, verbose_name=_("owner"))

    license = models.ForeignKey(License, null=True, blank=True, verbose_name=_("license"))

    created = models.DateTimeField(_('created'), auto_now=False, default=datetime.datetime.now)
    published = models.DateTimeField(_('published'), null=True)

    hidden = models.BooleanField(_('hidden'), default=False)
    permission = models.SmallIntegerField(_('permission'), null=False, default=0)

    description = models.TextField(_('description'), null=False, default='')
    cover = models.ImageField(_('cover'), upload_to=settings.COVER_IMAGE_UPLOAD_DIR, null=True)

    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '%s/%s/' % (settings.BOOKI_URL, self.url_title)

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
                if len(v) != 2:
                    return None

                try:
                    book_ver = emodels.BookVersion.objects.get(book=self, major=int(v[0]), minor=int(v[1]))
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

    def set_cover(self, filename):
        from booktype.utils.book import set_book_cover

        set_book_cover(self, filename)

    @property
    def metadata(self):
        return self.info_set.filter(
            Q(name__startswith=DC) | Q(name__startswith=DCTERMS) |
            Q(name__startswith=BKTERMS) | Q(name__startswith=ADD_META_TERMS)
        )

    @property
    def author(self):
        try:
            return self.info_set.get(name='DC.creator').value
        except Info.DoesNotExist:
            return self.owner.get_full_name()

    @author.setter
    def author(self, name):
        key, book, _string_type = 'DC.creator', self, 0

        meta, _ = Info.objects.get_or_create(
            book=book, name=key, kind=_string_type)
        meta.value_string = name
        meta.save()

    # DEPRECATED API NAMES
    getVersion = get_version
    getVersions = get_versions


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
class BaseInfo(models.Model):
    name = models.CharField(_('name'), max_length=2500, db_index=True)
    kind = models.SmallIntegerField(_('kind'), choices=INFO_CHOICES)

    value_string = models.CharField(_('value string'), max_length=2500, null=True)
    value_integer = models.IntegerField(_('value integer'), null=True)
    value_text = models.TextField(_('value text'), null=True)
    value_date = models.DateTimeField(_('value date'), auto_now=False, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

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

    # DEPRECATED API NAMES
    getValue = get_value


class Info(BaseInfo):
    """Basic model for saving book Metadata"""

    book = models.ForeignKey(
        Book, null=False,
        verbose_name=_("book")
    )

    class Meta:
        verbose_name = _('Metadata')
        verbose_name_plural = _('Metadata')

    @property
    def value(self):
        return self.get_value()


class BookSetting(BaseInfo):
    """Basic model for saving book settings"""

    book = models.ForeignKey(
        Book, null=False,
        verbose_name=_("book"),
        related_name='settings'
    )

    class Meta:
        verbose_name = _('Book setting')
        verbose_name_plural = _('Book settings')


# Book Version
class BookVersion(models.Model):
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    major = models.IntegerField(_('major'))
    minor = models.IntegerField(_('minor'))
    name = models.CharField(_('name'), max_length=50, blank=True)
    description = models.CharField(
        _('description'), max_length=250, blank=True)

    created = models.DateTimeField(
        _('created'), auto_now=False, null=False,
        default=datetime.datetime.now)
    # add published

    # this is for icejs tracking changes plugin
    track_changes = models.BooleanField(default=False)

    def get_toc(self):
        related_types = [
            'chapter', 'chapter__status',
            'chapter__lock', 'chapter__book',
            'chapter__version'
        ]

        return BookToc.objects.filter(version=self).select_related(*related_types).order_by("-weight")

    def get_hold_chapters(self):
        return Chapter.objects.filter(version=self, book=self.book, booktoc__chapter__isnull=True)

    def get_attachments(self):
        return Attachment.objects.filter(version=self)

    def get_version(self):
        return '%d.%d' % (self.major, self.minor)

    def get_absolute_url(self):
        return '%s/%s/_v/%s/' % (settings.BOOKI_URL, self.book.url_title, self.get_version())

    def __unicode__(self):
        return u'%d.%d (%s)' % (self.major, self.minor, self.name)

    # DEPRECATED API NAMES
    getTOC = get_toc
    getHoldChapters = get_hold_chapters
    getAttachments = get_attachments
    getVersion = get_version


# Chapter
class Chapter(models.Model):
    EDIT_PING_SECONDS_MAX_DELTA = 15

    version = models.ForeignKey(BookVersion, null=False, verbose_name=_('version'))
    book = models.ForeignKey(Book, null=False, verbose_name=_('book'))
    url_title = models.CharField(_('url title'), max_length=2500)
    title = models.CharField(_('title'), max_length=2500)
    status = models.ForeignKey(BookStatus, null=False, verbose_name=_('status'))

    # used to save statuses as checked
    checked_statuses = models.ManyToManyField(
        BookStatus, related_name='checked_statuses')

    assigned = models.CharField(_('assigned'), max_length=100, default='', blank=True)

    created = models.DateTimeField(_('created'), null=False, auto_now=False, default=datetime.datetime.now)
    modified = models.DateTimeField(_('modified'), null=True, auto_now=True)
    revision = models.IntegerField(_('revision'), default=1)
    content = models.TextField(_('content'))
    content_json = models.TextField(_('content json'), null=True, blank=True)

    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')

    def get_absolute_url(self):
        return '%s/%s/%s/' % (settings.BOOKI_URL, self.book.url_title, self.url_title)

    def __unicode__(self):
        return self.title

    @property
    def lock_type(self):
        """
        Return lock.type if exist, else return 0

        :Args:
          - self (:class:`booki.editor.models.Chapter`): Chapter instance

        :Returns:
          Int. Return lock.type value
        """
        try:
            # if ChapterLock was deleted in db but still have value in python object
            if self.lock.id:
                return self.lock.type
            return 0
        except ChapterLock.DoesNotExist:
            return 0

    @property
    def lock_username(self):
        """
        Return lock.user.username if exist, else return None

        :Args:
          - self (:class:`booki.editor.models.Chapter`): Chapter instance

        :Returns:
          username (:class:`str`) or None
        """
        try:
            # if ChapterLock was deleted in db but still have value in python object
            if self.lock.id:
                return self.lock.user.username
            return None
        except ChapterLock.DoesNotExist:
            return None

    def is_locked(self):
        """
        Return is chapter locked or not

        :Args:
          - self (:class:`booki.editor.models.Chapter`): Chapter instance

        :Returns:
          Return True or False
        """
        return bool(self.lock_type)

    def get_current_editor_username(self):
        """
        Return editor username who is editing chapter at the moment

        :Args:
          - self (:class:`booki.editor.models.Chapter`): Chapter instance

        :Returns:
          None (if chapter not under edit)
          or editor username (if chapter under edit)
        """
        edit_lock_key = "booktype:{book_id}:{version}:editlocks:{chapter_id}:*".format(
            book_id=self.book.id,
            version=self.version.get_version(),
            chapter_id=self.id
        )
        keys = sputnik.rkeys(edit_lock_key)

        if keys:
            # there is no sense to check last editor-ping and calculate time delta...
            # if chapter contains key in redis, this mean chapter still under edit
            # remote_ping or cellery deamon will check editor-ping time delta and remove key if needed

            # there is should be only one editor per book/version
            try:
                if len(keys) != 1:
                    raise Exception("Multiple keys were returned with KEYS: {0}".format(edit_lock_key))
            except Exception as e:
                logger.exception(e)
            finally:
                # get editor username from key
                username = keys[0].rsplit(':', 1)[-1]
                return username

        return None

    @property
    def has_comments(self):
        # excluding delete/resolved comments
        return self.comment_set.exclude(state=1).exists()

    @property
    def has_marker(self):
        if '[[' in self.content and ']]' in self.content:
            return True

        return False


class ChapterHistory(models.Model):
    chapter = models.ForeignKey(Chapter, null=False, verbose_name=_("chapter"))
    content = models.TextField()
    modified = models.DateTimeField(_('modified'), null=False, auto_now=True)
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    revision = models.IntegerField(_('revision'), default=1)
    comment = models.CharField(_('comment'), max_length=2500, blank=True)

    def __unicode__(self):
        return u'{0} | {1} - {2}. Comment: {3}'.format(
            self.chapter.book, self.chapter, self.modified, self.comment)

    class Meta:
        verbose_name = _('Chapter history')
        verbose_name_plural = ('Chapters history')

    def previous(self):
        lower = ChapterHistory.objects.filter(
                chapter=self.chapter, revision__lt=self.revision
            ).order_by('-revision')

        if lower.count() > 0:
            return lower.first().revision
        return None

    def next(self):
        higher = ChapterHistory.objects.filter(
                chapter=self.chapter, revision__gt=self.revision
            ).order_by('revision')

        if higher.count() > 0:
            return higher.first().revision
        return None


class ChapterLock(models.Model):
    LOCK_EVERYONE = 1
    LOCK_SIMPLE = 2
    LOCK_CHOICES = (
            (LOCK_EVERYONE, 'Lock everyone'),
            (LOCK_SIMPLE, 'Lock to people without permissions')
        )

    chapter = models.OneToOneField(Chapter, related_name='lock')
    user = models.ForeignKey(auth_models.User, verbose_name=_('user'))
    type = models.IntegerField(choices=LOCK_CHOICES, default=LOCK_SIMPLE)
    created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        verbose_name = _('Chapter Lock')
        verbose_name_plural = _('Chapters Locks')
        ordering = ('created',)

    def __unicode__(self):
        return u"{0} - {1}".format(self.chapter.title, self.get_type_display())


# Attachment
def upload_attachment_to(att, filename):
    return '%s/books/%s/%s/%s' % (
        settings.DATA_ROOT, att.book.url_title,
        att.version.get_version(), filename
    )


def get_attachment_url(att, filename):
    return '%sbooks/%s/%s/%s' % (
        settings.DATA_URL, att.book.url_title,
        att.version.get_version(), filename
    )


class AttachmentFile(models.FileField):
    def get_directory_name(self):
        # relative path
        name = super(models.FileField, self).get_directory_name()
        return name


class Attachment(models.Model):
    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("version"))
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    attachment = models.FileField(_('filename'), upload_to=upload_attachment_to, max_length=2500)
    status = models.ForeignKey(BookStatus, null=False, verbose_name=_("status"))
    created = models.DateTimeField(_('created'), null=False, auto_now=False, default=datetime.datetime.now)

    def delete(self):
        self.delete_thumbnail()
        self.attachment.delete(save=False)

        super(Attachment, self).delete()

    def __unicode__(self):
        return self.attachment.name

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    def get_name(self):
        name = self.attachment.name
        return name[name.rindex('/') + 1:]

    def thumbnail_name(self, size=(100, 100)):
        w, h = size
        filename, ext = os.path.splitext(os.path.basename(self.attachment.url))
        filename = '{}_{}_{}_{}x{}{}'.format(
            filename, self.pk, time.mktime(self.created.timetuple()), w, h, ext)
        return filename

    def thumbnail(self, size=(100, 100), aspect_ratio=False):
        """Returns URL for a thumbnail with the specified size"""
        from booktype.utils import misc

        filename = self.thumbnail_name(size)
        im_path = upload_attachment_to(self, filename)
        im_url = get_attachment_url(self, filename)

        if not os.path.exists(im_path):
            try:
                im = misc.create_thumbnail(self.attachment, size=size, aspect_ratio=aspect_ratio)
                # 8-bit pixels
                if im.mode == 'P':
                    im = im.convert('RGB')
                # 4x8-bit pixels, png for instance
                elif im.mode == 'RGBA':
                    # required for png.split()
                    im.load()
                    jpeg = Image.new("RGB", im.size, (255, 255, 255))
                    jpeg.paste(im, mask=im.split()[3])
                    im = jpeg
                im.save(im_path, 'JPEG', quality=100)
            except Exception as err:
                logger.exception('Can not create thumbnail. Error msg: %s' % err)
        return im_url

    def delete_thumbnail(self, size=(100, 100)):
        filename = self.thumbnail_name(size)
        thumb_path = upload_attachment_to(self, filename)

        try:
            os.remove(thumb_path)
        except Exception as err:
            logger.exception('Unable to delete thumbnail. Error msg: %s' % err)

    # DEPRECATED API NAMES
    getName = get_name


class BookToc(models.Model):
    # Book Toc
    SECTION_TYPE = 0
    CHAPTER_TYPE = 1
    LINE_TYPE = 2

    TYPEOF_CHOICES = (
        (SECTION_TYPE, _('section name')),
        (CHAPTER_TYPE, _('chapter name')),
        (LINE_TYPE, _('line'))
    )

    version = models.ForeignKey(BookVersion, null=False, verbose_name=_("version"))
    # book should be removed
    book = models.ForeignKey(Book, null=False, verbose_name=_("book"))
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=_("parent"))
    name = models.CharField(_('name'), max_length=2500, blank=True)
    chapter = models.ForeignKey(Chapter, null=True, blank=True, verbose_name=_("chapter"))
    weight = models.IntegerField(_('weight'))
    typeof = models.SmallIntegerField(_('typeof'), choices=TYPEOF_CHOICES)

    settings = models.TextField(_('settings'), blank=True)

    def is_section(self):
        return self.typeof == 0

    def is_chapter(self):
        return self.typeof == 1

    def has_children(self):
        return (self.booktoc_set.count() > 0)

    def children(self):
        return BookToc.objects.filter(parent=self)

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
        return u'%s %s ' % (self.user.username, self.permission)


class AttributionExclude(models.Model):
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))

    def __unicode__(self):
        return u'%s' % (self.user.username, )

    class Meta:
        verbose_name = _('Attribution Exclude')
        verbose_name_plural = _('Attribution Exclude')


class PublishWizzard(models.Model):
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))
    wizz_type = models.CharField(_('wizard type'), max_length=20, blank=False)
    wizz_options = models.TextField(_('wizard options'), default='', null=False)

    def __unicode__(self):
        return u'%s' % (self.book.url_title, )

    class Meta:
        verbose_name = _('Publish Wizard')
        verbose_name_plural = _('Publish Wizard')
        unique_together = ('book', 'user', 'wizz_type')


def upload_cover_to(att, filename):
    extension = os.path.splitext(filename)[-1].lower()
    return '%s/book_covers/%s%s' % (settings.DATA_ROOT, att.id, extension)


class BookCover(models.Model):
    book = models.ForeignKey(Book, null=True, verbose_name=_("book"))
    user = models.ForeignKey(auth_models.User, verbose_name=_("user"))

    cid = models.CharField('cid', max_length=40, null=False, default='', unique=True)

    attachment = models.FileField(_('filename'), upload_to=upload_cover_to, max_length=2500)
    filename = models.CharField('file name', max_length=250, unique=False, default='')
    title = models.CharField(_('Cover title'), max_length=250, blank=False, unique=False)

    width = models.IntegerField(_('Width'), blank=True, default=0)
    height = models.IntegerField(_('Height'), blank=True, default=0)
    unit = models.CharField(_('Unit'), max_length=20, blank=True, default='px')
    booksize = models.CharField(_('Booksize'), max_length=30, blank=True, default='')

    is_book = models.BooleanField(_('Book cover'), default=False)
    is_ebook = models.BooleanField(_('E-book cover'), default=False)
    is_pdf = models.BooleanField(_('PDF cover'), default=False)

    cover_type = models.CharField(_('Cover type'), max_length=20, blank=True)

    creator = models.CharField(_('Cover'), max_length=40, blank=True)
    license = models.ForeignKey(License, null=True, verbose_name=_("license"))

    notes = models.TextField(_('notes'))

    approved = models.BooleanField(_('Approved'), blank=False, default=False)

    created = models.DateTimeField(_('created'), auto_now_add=True)

    def delete(self):
        self.attachment.delete(save=False)

        super(BookCover, self).delete()

    def __unicode__(self):
        return u'%s' % (self.id, )


# DEPRECATED API NAMES
uploadAttachmentTo = upload_attachment_to
getAttachmentUrl = get_attachment_url
uploadCoverTo = upload_cover_to
