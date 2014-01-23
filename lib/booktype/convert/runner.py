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

import logging

from . import loader
from . import ConversionError
from .assets import AssetCollection


logger = logging.getLogger("booktype.convert")


def run_conversion(profile, input, output, config=None, sandbox_path=None, assets=None, converters=None, callback=None):
    if config is None:
        config = {}

    if sandbox_path is None:
        sandbox_path = os.path.abspath(os.curdir)

    if assets is None:
        assets = AssetCollection(sandbox_path)

    if converters is None:
        converters = loader.find_all()

    if not converters.has_key(profile):
        raise ConversionError("no converter registered for " + profile)

    book_asset = assets.get(input)

    if book_asset is None:
        raise ConversionError("no asset for input file '{}'".format(input))

    if not os.path.exists(sandbox_path):
        os.makedirs(sandbox_path)

    converter_class = converters[profile]
    converter = converter_class(config, assets, sandbox_path, callback)

    converter.validate_config()
    book = converter.load_book(book_asset.file_path)
    conversion_result = converter.convert(book, output)

    result = {
        "output" : output,
    }

    if isinstance(conversion_result, dict):
        result.update(conversion_result)

    return result
