from django.db import models
from django.utils.translation import ugettext_lazy as _

# Language

class Language(models.Model):
    name = models.CharField(_('name'), max_length=50, blank=False)
    abbrevation = models.CharField(_('abbrevation'), max_length=10, blank=False)

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')

# Project

STATUS_CHOICES = (
    (0, _('published')),
    (1, _('not published')),
    (2, _('not translated'))
)


## Project

class Project(models.Model):
    url_name = models.CharField(_('url_name'), max_length=20, blank=False)
    name = models.CharField(_('name'), max_length=100, blank=False)
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES) # change this
    created = models.DateTimeField(_('created'), auto_now=True)

    # put modified or published field also

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')


# Project Status

class ProjectStatus(models.Model):
    project = models.ForeignKey(Project, null=False)
    name = models.CharField(_('name'), max_length=30, blank=False)
    weight = models.SmallIntegerField(_('weight'))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Project status')
        verbose_name_plural = _('Project status')


# Book

class Book(models.Model):
    project = models.ForeignKey(Project, null=False)
    url_title = models.CharField(_('url_title'), max_length=20, blank=True) # can it be blank?
    title = models.CharField(_('title'), max_length=100, blank=False)
    status = models.ForeignKey(ProjectStatus, null=False)
    language = models.ForeignKey(Language, null=True) # can it be blank?
    created = models.DateTimeField(_('created'), auto_now=True)
    published = models.DateTimeField(_('published'), null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')


# Chapter

class Chapter(models.Model):
    book = models.ForeignKey(Book, null=False)
    url_title = models.CharField(_('url_title'), max_length=30)
    title = models.CharField(_('title'), max_length=200)
    status = models.ForeignKey(ProjectStatus, null=False) # this will probably change
    created = models.DateTimeField(_('created'), null=False)
    modified = models.DateTimeField(_('modified'), null=True)

    # missing licence here
    content = models.TextField()

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')


# Attachment

def uploadAttachmentTo(att, filename):
    from booki import settings
    # use MEDIA_ROOT
    return '%s%s/%s' % (settings.MEDIA_ROOT, att.book.url_title, filename)


class Attachment(models.Model):
    book = models.ForeignKey(Book, null=False)
    attachment = models.FileField(_('filename'), upload_to=uploadAttachmentTo)
    status = models.ForeignKey(ProjectStatus, null=False)
    created = models.DateTimeField(_('created'), null=False, auto_now=True)

#>>> from django.core.files import File
#
#>>> f = open('/tmp/hello.world', 'w')
#>>> myfile = File(f)

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
    book = models.ForeignKey(Book, null=False)
    name = models.CharField(_('name'), max_length=100, blank=True)
    chapter = models.ForeignKey(Chapter, null=True, blank=True)
    weight = models.IntegerField(_('weight'))
    typeof = models.SmallIntegerField(_('typeof'), choices=TYPEOF_CHOICES)

    def __unicode__(self):
        return unicode(self.weight)


    class Meta:
        verbose_name = _('Book TOC')
        verbose_name_plural = _('Book TOCs')


