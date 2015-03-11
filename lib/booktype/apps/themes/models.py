from django.db import models
from django.contrib.auth import models as auth_models

from booki.editor.models import Book

class UserTheme(models.Model):
    book   = models.ForeignKey(Book, null=False, verbose_name='book')
    owner  = models.ForeignKey(auth_models.User, verbose_name='owner', default=None, null=True)
    custom = models.TextField("custom", default='{}', null=False)
    active = models.CharField("active", default="custom", max_length=32)

    def __unicode__(self):
        return self.custom
