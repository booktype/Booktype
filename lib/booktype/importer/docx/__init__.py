# -*- coding: utf-8 -*-
import os
import tempfile
from booktype.importer.docx.utils import get_importer_class


def import_docx(docx_file, book, notifier=None, delegate=None, options=None):
    """
    Imports a DOCX book.
    """

    # obtain correct importer class
    importer = get_importer_class()(book=book)

    if delegate:
        importer.delegate = delegate
    if notifier:
        importer.notifier = notifier

    # file on disk
    if isinstance(docx_file, file):
        importer.import_file(docx_file.name, options=options)

    # path to file on disk
    elif isinstance(docx_file, str) or isinstance(docx_file, unicode):
        importer.import_file(docx_file, options=options)

    # some file-like object
    elif isinstance(docx_file, object):
        temp_file = tempfile.NamedTemporaryFile(
            prefix="booktype-", suffix=".docx", delete=False)
        for chunk in docx_file:
            temp_file.write(chunk)
        temp_file.close()

        importer.import_file(temp_file.name, options=options)
        os.remove(temp_file.name)
