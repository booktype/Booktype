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

import celery
import logging

from django.core.files import File
from django.template.defaultfilters import slugify


logger = logging.getLogger("booktype.apps.convert")


class AssetCollection(object):
    def __init__(self, base_path):
        self.base_path = base_path
        self.files = {}

    def add_files(self, files):
        for (asset_id, file_path) in files.iteritems():
            self.files[asset_id] = AssetFile(asset_id, file_path)

    def add_urls(self, urls):
        for (asset_id, url) in urls.iteritems():
            file_path = os.path.join(self.base_path, slugify(asset_id))
            download(url, file_path)
            self.files[asset_id] = AssetFile(asset_id, file_path, original_url=url)

    def __repr__(self):
        return repr(self.files)


class AssetFile(object):
    def __init__(self, asset_id, file_path, original_url=None):
        self.asset_id     = asset_id
        self.file_path    = file_path
        self.file_url     = "file://" + file_path
        self.original_url = original_url

    def __repr__(self):
        return "<%s %s: %s>" % ("AssetFile", repr(self.asset_id), repr(self.file_path))


class Task(celery.Task):
    def __init__(self):
        celery.Task.__init__(self)
        os.putenv("LC_ALL", "en_US.UTF-8")


def task(func):
    """Default decorator for all task functions.
    """
    @celery.task(base = Task, name = func.__name__)
    def decorated_func(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return decorated_func


def download(src_url, dst_file):
    import urllib2
    src = urllib2.urlopen(src_url)
    try:
        with open(dst_file, "w") as dst:
            for chunk in src:
                dst.write(chunk)
    finally:
        src.close()


@task
def convert_one(profile, config, book, output):
    result = {
        "status" : "ok",
    }
    return result


@task
def convert(request_data, sandbox_path):
    assets = AssetCollection(sandbox_path)

    assets.add_urls(request_data.assets)
    assets.add_files(request_data.files)
    logger.debug(assets)

    result = {
        "status" : "ok",
    }
    return result


__all__ = ("convert", )
