import os
import tempfile

from django.http import HttpResponse

from django.views.generic.base import View

from booki.editor import models
from . import utils


class SaveView(utils.RestrictExport, View):
    def get(self, request, bookid):

        try:
            book = models.Book.objects.get(url_title__iexact=bookid)
        except models.Book.DoesNotExist:
            pass

        book_version = book.get_version(None)

        response = HttpResponse(content_type='application/epub+zip')
        response['Content-Disposition'] = 'attachment; filename=%s.epub' % book.url_title

        temp_dir = tempfile.mkdtemp()
        filename = '%s/export.epub' % temp_dir

        from booktype.apps.export.utils import export_book

        # it should return object epub book
        # we should be able to write it as a separate thing
        export_book(filename, book_version)

        # write file
        response.write(open(filename, 'rb').read())

        os.unlink(filename)
        os.rmdir(temp_dir)

        return response
