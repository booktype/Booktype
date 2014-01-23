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

from ebooklib import epub

from ..base import BaseConverter
from ..utils import run_command
from .. import ConversionError


class MobiConverter(BaseConverter):
    name = "mobi"

    def convert(self, book, output_path):
        epub_path = os.path.join(self.sandbox_path, "book.epub")

        if os.path.exists(epub_path):
            epub_file = tempfile.NamedTemporaryFile(prefix="book-", suffix=".epub", dir=self.sandbox_path, delete=False)
            epub_path = epub_file.name

        epub_writer = epub.EpubWriter(epub_path, book)
        epub_writer.process()
        epub_writer.write()

        command = ["kindlegen", "-o", output_path, epub_path]
        rc, out, err = run_command(command)

        if rc != 0:
            raise ConversionError("error running external command '{}'".format( command[0]))
