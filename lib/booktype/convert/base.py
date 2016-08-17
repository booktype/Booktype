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

from ebooklib import epub
from booktype.apps.convert.plugin import SectionsSettingsPlugin


class BaseConverter(object):
    """
    This is the base converter class. All output converters should inherit from
    this class so they have at least the basic methods to be a converter
    """

    def __init__(self, config, assets, sandbox_path, callback, options=None):
        self._config = config
        self._assets = assets
        self._sandbox_path = sandbox_path
        self._callback = callback

        self.options = dict({
            'plugins': [SectionsSettingsPlugin(self)]
        })

        if options:
            self.options.update(options)

    @property
    def config(self):
        return self._config

    @property
    def assets(self):
        return self._assets

    @property
    def sandbox_path(self):
        return self._sandbox_path

    @property
    def callback(self):
        return self._callback

    def validate_config(self):
        pass

    def load_book(self, book_path):
        return epub.read_epub(book_path)

    def pre_convert(self, original_book):
        for plg in self.options.get('plugins', []):
            if hasattr(plg, 'pre_convert'):
                plg.pre_convert(original_book)

    def convert(self, book, output_path):
        pass

    def post_convert(self, book, output_path):
        for plg in self.options.get('plugins', []):
            if hasattr(plg, 'post_convert'):
                plg.post_convert(book, output_path)

    def get_asset(self, asset_id):
        return self.assets.get(asset_id)

    def open_file(self, file_name, mode="wb"):
        file_path = os.path.join(self.sandbox_path, file_name)
        return open(file_path, mode)
