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
from lxml import etree

from django.utils.translation import ugettext_lazy as _

from booktype.convert.image_editor_conversion import ImageEditorConversion

from ..mpdf.converter import MPDFConverter
from ..utils.epub import reformat_endnotes

logger = logging.getLogger("booktype.convert.screenpdf")


class ScreenPDFConverter(MPDFConverter):
    name = 'screenpdf'
    verbose_name = _("Screen PDF")
    support_section_settings = True
    images_color_model = "RGB"

    def __init__(self, *args, **kwargs):
        super(ScreenPDFConverter, self).__init__(*args, **kwargs)

    def pre_convert(self, epub_book):
        super(ScreenPDFConverter, self).pre_convert(epub_book)

        # create image edtor conversion instance
        # todo move it to more proper place in the future, and create plugin for it

        # calculate pdf document width
        mm = float(self.config['page_width_bleed'])
        mm -= float(self.config['settings'].get('side_margin', 0)) + float(self.config['settings'].get('gutter', 0))
        inches = mm / 10 / 2.54

        self._bk_image_editor_conversion = ImageEditorConversion(
            epub_book, inches * 300, self
        )

    def get_extra_configuration(self):
        data = {'mirror_margins': False}

        # get additional mpdf configuration options
        data.setdefault('mpdf', {}).update(self._get_theme_mpdf_config())

        return data

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

    def _reformat_endnotes(self, chapter_content):
        """Insert internal link to endnote's body into the sup tag.

        :Args:
          - chapter_content: lxml node tree with the chapter content

        """

        reformat_endnotes(chapter_content)

        # add tag 'a' with 'name' attribute equal to 'li.id' attribute
        for li in chapter_content.xpath('//li[starts-with(@id, "endnote-")]'):
            a = etree.Element("a")
            a.set('name', li.get('id'))
            a.tail = li.text
            a.text = ''
            li.text = ''
            li.insert(0, a)

    def _fix_content(self, content):
        if content is None:
            return content

        self._reformat_endnotes(content)
        self._fix_columns(content)

        return content
