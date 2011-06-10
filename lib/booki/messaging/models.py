
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
        verbose_name = _('PostAppearance')
        verbose_name_plural = _('PostAppearances')


class Endpoint(models.Model):
    syntax = models.CharField(_('syntax'), max_length=2500, unique=True)

    def as_user(self):
        if not self.syntax.startswith("@"):
            return None

        users = auth_models.User.objects.filter(username=self.syntax[1:])
        if len(users) == 1:
            return users[0]
        else:
            return None

    def __unicode__(self):
        return self.syntax

    class Meta:
        verbose_name = _('Endpoint')
        verbose_name_plural = _('Endpoints')


class Following(models.Model):
    follower = models.ForeignKey('Endpoint', verbose_name=_("follower"), related_name='follower')
    target = models.ForeignKey('Endpoint', verbose_name=_("target"), related_name='target')

    def __unicode__(self):
        return u"%s-%s" % (self.follower, self.target)

    class Meta:
        verbose_name = _('Following')
        verbose_name_plural = _('Followings')
