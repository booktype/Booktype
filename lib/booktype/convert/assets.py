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
import requests

from django.template.defaultfilters import slugify

from booktype.utils import config


class AssetCollection(object):

    def __init__(self, base_path):
        self.base_path = base_path
        self.files = {}

    def add_files(self, files):
        for (asset_id, file_path) in files.items():
            self.files[asset_id] = AssetFile(asset_id, file_path)

    def add_urls(self, urls):
        for (asset_id, url) in urls.items():
            file_path = os.path.join(self.base_path, slugify(asset_id))
            download(url, file_path)
            self.files[asset_id] = AssetFile(asset_id, file_path, original_url=url)

    def get(self, asset_id):
        return self.files.get(asset_id)

    def __repr__(self):
        return repr(self.files)


class AssetFile(object):

    def __init__(self, asset_id, file_path, original_url=None):
        self.asset_id = asset_id
        self.file_path = file_path
        self.file_url = "file://" + file_path
        self.original_url = original_url

    def __repr__(self):
        return "<%s %s: %s>" % ("AssetFile", repr(self.asset_id), repr(self.file_path))


def download(src_url, dst_file):
    req = requests.get(src_url, stream=True, verify=config.get_configuration('REQUESTS_VERIFY_SSL_CERT'))

    if req.status_code == 200:
        with open(dst_file, 'wb') as dst:
            for chunk in req:
                dst.write(chunk)
