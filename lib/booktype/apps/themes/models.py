from django.db import models

from booki.editor.models import Book


class BookTheme(models.Model):
    book = models.OneToOneField(Book)
    active = models.CharField(max_length=32)
    custom = models.TextField(default='{}')

    def __str__(self):
        return '{} in book: "{}"'.format(self.active, self.book.title)
