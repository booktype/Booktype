# -*- coding: utf-8 -*-
import json
from datetime import date
from django.db import models
from django.contrib.auth.models import User

from booki.editor.models import Chapter, Book, BookToc
from booktype.apps.core.models import Role


class Comment(models.Model):
    """Model for storing Word comments"""

    # Every comment is connected with certain chapter document
    chapter = models.ForeignKey(Chapter, null=False, verbose_name="chapter")

    # Comments can have parents. This is when one user participates in the discussion
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    # Word .docx files have comment_id. In Word file they are strings.
    comment_id = models.CharField("cid", max_length=50, null=False, unique=True)

    # Name of the author. In case we are importing from Word
    author = models.CharField("author", max_length=50, default='', null=False)

    # user who created the comment if any
    user = models.ForeignKey(User, null=True)

    # Date when comments was written
    date = models.DateTimeField("date", null=False)

    # Content of the comment
    content = models.TextField("content", default='', null=False)

    # Text we are commenting on
    text = models.TextField("text", default='', null=False)

    # Status of the comment
    # 0 - default
    # 1 - resolved
    # 2 - ??
    status = models.PositiveSmallIntegerField('status', default=0, null=False)

    # State of the comment
    # 0 - default
    # 1 - deleted
    # 2 - ??
    state = models.PositiveSmallIntegerField('state', default=0, null=False)

    # Was this comment imported from Word file?
    is_imported = models.BooleanField('is_imported', default=False, null=False)

    # we mark this field to know if user has saved the chapter reference
    stored_reference = models.BooleanField(default=False)

    @property
    def children(self):
        return Comment.objects.filter(parent=self)

    @property
    def get_author(self):
        from django.conf import settings
        from booktype.apps.account import utils

        if self.user:
            return {
                'name': self.user.get_full_name() or self.user.username,
                'avatar': utils.get_profile_image(self.user, 35)
            }
        else:
            return {
                'name': self.author,
                'avatar': '{}{}'.format(settings.STATIC_URL, 'account/images/anonymous.png')
            }


class InviteCode(models.Model):
    """
    This model will be used to store information about code invitations
    Codes should be expirable and every person that uses a code will be assigned
    to the given book, related here, as the given roles related also here
    """

    code = models.CharField(max_length=20, unique=True, db_index=True)
    book = models.ForeignKey(Book, related_name='invite_codes')
    roles = models.ManyToManyField(Role, verbose_name='Roles to assign')
    created = models.DateTimeField(auto_now_add=True)
    expire_on = models.DateField()

    @property
    def roles_as_string(self):
        return ", ".join(self.roles.all().values_list('name', flat=True))

    @property
    def expired(self):
        now = date.today()
        return now > self.expire_on


class ChatThread(models.Model):
    """
    Chat thread. All messages go here.
    In future book can have more than 1 thread,
    that is why we have this proxy model.
    """
    book = models.ForeignKey(Book)

    def __str__(self):
        return '"{}" thread.'.format(self.book.title)


class ChatMessage(models.Model):
    """
    Chat message.
    """
    thread = models.ForeignKey(ChatThread, related_name='messages')
    sender = models.ForeignKey(User)
    text = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return '{} Message from {} at {}.'.format(self.thread, self.sender, self.datetime)


# post user save hook
def default_section_settings(sender, instance, created, **kwargs):
    """
    Django signal that fires when BookToc model is being saved.

    This will only set "mark_section_as" setting to "mainmatter" to
    newly created Sections
    """

    SECTION_TYPE = 0

    if created and instance.typeof == SECTION_TYPE:
        instance.settings = json.dumps({"mark_section_as": "mainmatter"})
        instance.save()

models.signals.post_save.connect(default_section_settings, sender=BookToc)
