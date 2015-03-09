# -*- coding: utf-8 -*-
import os
import tempfile
from .docximporter import WordImporter


def import_docx(docx_file, book, notifier=None, delegate=None,
                options=None, language='en'):
    """
    Imports a DOCX book.
    """

    importer = WordImporter()
    importer.language = language

    if delegate:
        importer.delegate = delegate
    if notifier:
        importer.notifier = notifier

    if isinstance(docx_file, file):
        # file on disk
        importer.import_file(docx_file.name, book, options)
    elif isinstance(docx_file, str) or isinstance(docx_file, unicode):
        # path to file on disk
        importer.import_file(docx_file, book, options)
    elif isinstance(docx_file, object):
        # some file-like object

        temp_file = tempfile.NamedTemporaryFile(
            prefix="booktype-", suffix=".docx", delete=False)
        for chunk in docx_file:
            temp_file.write(chunk)
        temp_file.close()

        importer.import_file(temp_file.name, book, options)

        os.remove(temp_file.name)
