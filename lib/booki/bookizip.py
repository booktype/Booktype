# This file is part of Booktype.
# Copyright (c) 2012 Douglas Bagnall
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

import os, sys

from booki.utils.json_wrapper import json

from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED

MEDIATYPES = {
    'html': "text/html",
    'xhtml': "application/xhtml+xml",
    'css': 'text/css',
    'json': "application/json",

    'png': 'image/png',
    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'svg': 'image/svg+xml',
    'tiff': 'image/tiff',

    'ncx': 'application/x-dtbncx+xml',
    'dtb': 'application/x-dtbook+xml',
    'xml': 'application/xml',

    'pdf': "application/pdf",
    'txt': 'text/plain',

    'epub': "application/epub+zip",
    'booki': "application/x-booki+zip",

    None: 'application/octet-stream',
}

#metadata construction routines
DC = "http://purl.org/dc/elements/1.1/"
FM = "http://booki.cc/"

def get_metadata(metadata, key, ns=DC,
                 scheme='', default=[]):
    """Get a list of metadata values matching a key, namespace and
    scheme.  If the ns or scheme are not set, they default to Dublin
    Core and an empty string, respectively.

    If no values are set, an empty list is returned, unless the
    default argument is given, in which case you get that.
    """
    values = metadata.get(ns, {}).get(key, {})
    if scheme == '*':
        return sum(values.values(), [])
    return values.get(scheme, default)

def get_metadata_schemes(metadata, key, ns=DC):
    """Say what schemes are available for a given key and namespace."""
    values = metadata.get(ns, {}).get(key, {})
    return values.keys()

def add_metadata(metadata, key, value, ns=DC, scheme=''):
    """Add a metadata (ns, key, scheme, value) tuple. Namespace
    defaults to Dublin Core, and scheme to an empty string.  In most
    cases that is what you want."""
    namespace = metadata.setdefault(ns, {})
    items = namespace.setdefault(key, {})
    values = items.setdefault(scheme, [])
    values.append(value)

def clear_metadata(metadata, key, ns=DC, scheme='*'):
    """Clear metadata for a key in a namespace (ns).  If namespace is
    ommited, Dublin Core is assumed.  If a scheme is specified (and is
    not '*'), only metadata in that scheme is removed.  By default all
    schemes are removed.

    If ns is '*', that key is removed from all namespaces.
    """
    if ns in metadata:
        if key in metadata[ns]:
            if scheme == '*':
                metadata[ns][key] = {}
            elif scheme in metadata[ns][key]:
                del metadata[ns][key][scheme]
        elif ns == '*':
            for ns in metadata:
                clear_metadata(metadata, key, ns, scheme)


class BookiZip(object):
    """Helper for writing booki-zips"""

    def __init__(self, filename, info={}):
        """Start a new zip and put an uncompressed 'mimetype' file at the
        start.  This idea is copied from the epub specification, and
        allows the file type to be dscovered by reading the first few
        bytes."""
        self.zipfile = ZipFile(filename, 'w', ZIP_DEFLATED, allowZip64=True)
        self.write_blob('mimetype', MEDIATYPES['booki'], ZIP_STORED)
        self.filename = filename
        self.manifest = {}
        self.info = info

    def write_blob(self, filename, blob, compression=ZIP_DEFLATED, mode=0644):
        """Add something to the zip without adding to manifest"""
        zinfo = ZipInfo(filename)
        zinfo.external_attr = mode << 16L # set permissions
        zinfo.compress_type = compression
        self.zipfile.writestr(zinfo, blob)

    def add_to_package(self, ID, fn, blob, mediatype=None,
                       contributors=[], rightsholders=[], license=[]):
        """Add an item to the zip, and save it in the manifest.  If
        mediatype is not provided, it will be guessed according to the
        extrension."""
        self.write_blob(fn, blob)
        if mediatype is None:
            ext = fn[fn.rfind('.') + 1:]
            mediatype = MEDIATYPES.get(ext, MEDIATYPES[None])
        self.manifest[ID] = {
            "url":           fn,
            "mimetype":      mediatype,
            "contributors":  contributors,
            "rightsholders": rightsholders,
            "license":       license,
            }

    def _close(self):
        self.zipfile.close()

    def finish(self):
        """Finalise the metadata and write to disk"""
        self.info['manifest'] = self.manifest
        infojson = json.dumps(self.info, indent=2)
        self.add_to_package('info.json', 'info.json', infojson, 'application/json')
        self._close()

