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

import logging

from ..mpdf.converter import MPDFConverter


logger = logging.getLogger("booktype.convert.screenpdf")


class ScreenPDFConverter(MPDFConverter):
    name = "screenpdf"

    def __init__(self, *args, **kwargs):
        super(ScreenPDFConverter, self).__init__(*args, **kwargs)

    def get_extra_configuration(self):        
        return {'mirror_margins': False}

    def get_extra_style(self, book):
        cover_image = ''

        if 'cover_image' in self.config:
            cover_asset = self.get_asset(self.config['cover_image'])            
            cover_image = cover_asset.file_path

        return {'cover_image': cover_image}

    def get_extra_data(self, book):
        data = super(ScreenPDFConverter, self).get_extra_data(book)

        if 'cover_image' in self.config:
            cover_asset = self.get_asset(self.config['cover_image'])
            data['cover_image'] = cover_asset.file_path
        else:
            data['cover_image'] = ''

        return data

    def _fix_content(self, content):
        if content is None:
            return content

        self._fix_broken_endnotes(content)
        self._fix_columns(content)

        return content
