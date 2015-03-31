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

        response = HttpResponse(mimetype='application/epub+zip')
        response['Content-Disposition'] = 'attachment; filename=%s.epub' % book.url_title

        tempDir = tempfile.mkdtemp()
        fileName = '%s/export.epub' % tempDir

        from booktype.utils.misc import export_book

        # it should return object epub book
        # we should be able to write it as a separate thing
        export_book(fileName, book_version)

        # write file
        response.write(open(fileName, 'rb').read())

        os.unlink(fileName)
        os.rmdir(tempDir)

        return response
