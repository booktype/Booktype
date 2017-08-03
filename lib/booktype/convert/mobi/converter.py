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

from django.utils.translation import ugettext_lazy as _

from booktype.utils import config
from booktype.convert.image_editor_conversion import ImageEditorConversion

from ..utils import run_command
from .. import ConversionError
from ..epub.converter import Epub3Converter


MOBI_DOCUMENT_WIDTH = config.get_configuration('MOBI_DOCUMENT_WIDTH')


class MobiConverter(Epub3Converter):
    name = 'mobi'
    verbose_name = _('MOBI')
    support_section_settings = True

    def pre_convert(self, original_book, book):
        super(MobiConverter, self).pre_convert(original_book, book)

        # create image editor conversion instance
        # todo move it to more proper place in the future, and create plugin for it
        self._bk_image_editor_conversion = ImageEditorConversion(
            original_book, MOBI_DOCUMENT_WIDTH, self
        )

    def convert(self, book, output_path):
        super(MobiConverter, self).convert(book, output_path + '.epub')

        mobi_convert = config.get_configuration('MOBI_CONVERT')

        if mobi_convert == 'kindlegen':
            kindlegen_path = config.get_configuration('KINDLEGEN_PATH')
            command = [kindlegen_path, "-o", output_path.name, output_path + '.epub']
        elif mobi_convert == 'calibre':
            calibre_path = config.get_configuration('CALIBRE_PATH')
            calibre_args = config.get_configuration('CALIBRE_ARGS')

            command = [calibre_path, output_path + '.epub', output_path]
            if calibre_args != '':
                command += [calibre_args]

        rc, out, err = run_command(command)

        if rc not in [0, 1]:
            raise ConversionError("error running external command '{}'".format( command[0]))

        return {"size": os.path.getsize(output_path)}
