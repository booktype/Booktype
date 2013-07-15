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


def run_conversion(profile, book, output, config=None, sandbox_path=None, assets=None, converters=None, callback=None):
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

    converter = converters[profile]()

    logger.debug(assets)
    logger.debug(converter)

    # TODO: run the converter
    #
    import time
    for i in range(0, 3):
        if callable(callback):
            callback({"bla" : i })
        time.sleep(2)

    result = {
        "status" : "ok",
        "output" : output,
    }
    return result

