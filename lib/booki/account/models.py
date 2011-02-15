from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

## UserProfile

from django.core.files.storage import FileSystemStorage

#fs = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)

class UserProfile(models.Model):
    """
    Booki user profile. Has additional information about user.

    @ivar mood: Status message for user.
    @ivar image: Profile image for user.
    @ivar description: "More" about this user.
    @ivar user: Reference to C{User}.
    """

#    image = models.ImageField(upload_to=settings.PROFILE_IMAGE_UPLOAD_DIR, null=True, storage=fs)
    mood = models.CharField(_('mood'), max_length=1000, blank=True, null=False, default='')
    image = models.ImageField(_('image'), upload_to=settings.PROFILE_IMAGE_UPLOAD_DIR, null=True)
    description = models.CharField(_('description'), max_length=2500, blank=False,null=False,default='')
    user = models.ForeignKey(User, unique=True, verbose_name=_("user"))

class UserPassword(models.Model):
    """
    Stores data when user starts process of password changing.

    @ivar user: Reference to C{User}.
    @ivar secretcode: Randomly generated password.
    @ivar created: Timestamp when user started process of password changing.

    @ivar remote_useragent: Client user agent.
    @ivar addr: Client address.
    @ivar host: Client host.
    """

    user = models.ForeignKey(User, unique=False, verbose_name=_("user"))
    secretcode = models.CharField(_('secretcode'), max_length=30, blank=False, null=False)
    created = models.DateTimeField(_('created'), auto_now=True)

    remote_useragent = models.CharField(_('remote useragent'), max_length=1000, blank=True, null=False, default='')
    remote_addr = models.CharField(_('remote addr'), max_length=1000, blank=True, null=False, default='')
    remote_host = models.CharField(_('remote host'), max_length=1000, blank=True, null=False, default='')


# post user save hook

def add_user_profile ( sender, instance, created, **kwargs ):
    """
    Django signal that fires when User model is being saved.
    """

    if created:
        user_profile = UserProfile(user = instance)
        user_profile.save()

models.signals.post_save.connect (add_user_profile, sender = User)
