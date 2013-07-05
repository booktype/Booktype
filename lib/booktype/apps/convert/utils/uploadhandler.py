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

import django.core.files
from django.template.defaultfilters import slugify


class UploadedFile(django.core.files.uploadedfile.UploadedFile):
    def __init__(self, path, content_type, size, charset):
        file = open(path, "wb")
        super(UploadedFile, self).__init__(file, file.name, content_type, size, charset)

    def file_path(self):
        return self.file.name

    def close(self):
        return self.file.close()


class FileUploadHandler(django.core.files.uploadhandler.FileUploadHandler):
    def __init__(self, base_path, *args, **kwargs):
        self.base_path = base_path
        super(FileUploadHandler, self).__init__(*args, **kwargs)

    def new_file(self, *args, **kwargs):
        super(FileUploadHandler, self).new_file(*args, **kwargs)
        file_path = os.path.join(self.base_path, slugify(self.field_name))
        self.file = UploadedFile(file_path, content_type=self.content_type, size=0, charset=self.charset)

    def receive_data_chunk(self, raw_data, start):
        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file
