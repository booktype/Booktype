# This file is part of Booktype.
# Copyright (c) 2013 Borko Jandras <borko.jandras@sourcefabric.org>
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

import os
import tempfile

from .epubimporter import EpubImporter


def import_epub(epub_file, book, notifier=None, delegate=None):
    """
    Imports the EPUB book.
    """

    importer = EpubImporter()

    if delegate:
        importer.delegate = delegate
    if notifier:
        importer.notifier = notifier

    if isinstance(epub_file, file):
        # file on disk
        importer.import_file(epub_file.name, book)
    elif isinstance(epub_file, str) or isinstance(epub_file, unicode):
        # path to file on disk
        importer.import_file(epub_file, book)
    elif isinstance(epub_file, object):
        # some file-like object

        temp_file = tempfile.NamedTemporaryFile(prefix="booktype-", suffix=".epub", delete=False)
        for chunk in epub_file:
            temp_file.write(chunk)
        temp_file.close()

        importer.import_file(temp_file.name, book)

        os.remove(temp_file.name)
