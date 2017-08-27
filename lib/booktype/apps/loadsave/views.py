import os
import tempfile

from django.http import HttpResponse

from django.views.generic.base import View

from booki.editor import models
from . import utils


class SaveView(utils.RestrictExport, View):
    """
    Simple view that serves a given book as epub file.
    This is our base raw epub for converter scripts
    """

    def get_filename(self, book):
        return book.url_title

    def get(self, request, bookid):

        try:
            book = models.Book.objects.get(url_title__iexact=bookid)
        except models.Book.DoesNotExist:
            pass

        book_version = book.get_version(None)

        response = HttpResponse(content_type='application/epub+zip')
        response['Content-Disposition'] = 'attachment; filename=%s.epub' % self.get_filename(book)

        temp_dir = tempfile.mkdtemp()
        filename = '%s/export.epub' % temp_dir

        from booktype.apps.export.utils import get_exporter_class

        # it should return object epub book
        # we should be able to write it as a separate thing
        get_exporter_class()(filename, book_version).run()

        # write file
        response.write(open(filename, 'rb').read())

        os.unlink(filename)
        os.rmdir(temp_dir)

        return response


class SaveAsEpubSkeleton(SaveView):
    """
    Just to set custom filename in order to differentiate
    this epub from on of the publish panel.
    """

    def get_filename(self, book):
        return "{}_EPUB_SKELETON".format(book.url_title)
