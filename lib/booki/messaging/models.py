# This file is part of Booktype.
# Copyright (c) 2012  Seravo Oy <tuukka@seravo.fi>
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
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from django.core.urlresolvers import reverse
from django.utils.html import escape

def uploadAttachmentTo(message, filename):
    return 'messages/%s/%s' % (message.sender.as_user().username, filename)

# XXX class "Message" with field "sender" would cause Django Admin to crash...
class Post(models.Model):
    sender = models.ForeignKey("Endpoint", verbose_name=_("sender"))
    timestamp = models.DateTimeField(_('timestamp'), null=False, auto_now=True)
    content = models.TextField(_('content'))
    attachment = models.FileField(_('attachment'), upload_to=uploadAttachmentTo, max_length=2500)
    snippet = models.TextField(_('snippet'))
    context_url = models.TextField(_('context'))

    def content_as_html(self):
        res = []
        for part in self.content.split():
            url = None
            if part.startswith("@"):
                url = reverse("view_profile", args=[part[1:]])
            elif part.startswith("!"):
                url = reverse("view_group", args=[part[1:]])
            elif part.startswith(u"\u212c"):
                url = reverse("view_book", args=[part[1:]])
            elif part.startswith("#"):
                url = reverse("view_tag", args=[part[1:]])
            part = escape(part)
            if url:
                part = '<a href="%s">%s</a>' % (escape(url), part)
            res.append(part)
        return " ".join(res)

    def __unicode__(self):
        return u"%s-%s" % (self.sender, self.timestamp)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')


class PostAppearance(models.Model):
    post = models.ForeignKey('Post', verbose_name=_("post"))
    timestamp = models.DateTimeField(_('timestamp'), null=False)
    endpoint = models.ForeignKey('Endpoint', verbose_name=_('endpoint'))

    def __unicode__(self):
        return u"%s-%s-%s" % (self.post.sender, self.endpoint, self.timestamp)

    class Meta:
        verbose_name = _('Post appearance')
        verbose_name_plural = _('Post appearances')

def match_wildcard(pattern, word):
    if pattern == word:
        return True
    if pattern[-1] == "*" and word.startswith(pattern[:-1]):
        return True
    return False

class Endpoint(models.Model):
    syntax = models.CharField(_('syntax'), max_length=2500, unique=True)
    config = models.ForeignKey('EndpointConfig', unique=True, null=True, blank=True)

    def as_user(self):
        if not self.syntax.startswith("@"):
            return None

        users = auth_models.User.objects.filter(username=self.syntax[1:])
        if len(users) == 1:
            return users[0]
        else:
            return None

    def notification_filter(self):
        if self.config:
            return self.config.notification_filter
        else:
            try:
                return settings.DEFAULT_NOTIFICATION_FILTER
            except AttributeError:
                return ""

    def get_config(self):
        if not self.config:
            config = EndpointConfig()
            config.save()
            self.config = config
            self.save()
        return self.config

    def wants_notification(self, message, word):
        filters = self.notification_filter().split(" ")

        if word == self.syntax: # if direct message:
            word = message.sender.syntax # then filter based on sender

        for f in filters:
            if not f:
                continue

            if f == "*":
                return False # filter out all

            if word:
                if match_wildcard(f, word):
                    return False
            else:
                # the notification is because of following a user
                if f[0]=="~" and match_wildcard(f[1:], message.sender.syntax[1:]):
                    return False

            # filter based on sender if f is plain username:
            if match_wildcard(f, message.sender.syntax[1:]):
                return False

        return True # no filters matched

    def __unicode__(self):
        return self.syntax

    class Meta:
        verbose_name = _('Endpoint')
        verbose_name_plural = _('Endpoints')

class EndpointConfig(models.Model):
    notification_filter = models.CharField(_('notification filter'), max_length=2500, blank=True)

    def __unicode__(self):
        return "config-"+"-".join(str(x) for x in self.endpoint_set.all())

    class Meta:
        verbose_name = _('Endpoint config')
        verbose_name_plural = _('Endpoint configs')

class Following(models.Model):
    follower = models.ForeignKey('Endpoint', verbose_name=_("follower"), related_name='follower')
    target = models.ForeignKey('Endpoint', verbose_name=_("target"), related_name='target')

    def __unicode__(self):
        return u"%s-%s" % (self.follower, self.target)

    class Meta:
        verbose_name = _('Following')
        verbose_name_plural = _('Followings')
