import os, sys

try:
    import simplejson as json
except ImportError:
    import json

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

    'ncx': 'application/x-dtbncx+xml',
    'dtb': 'application/x-dtbook+xml',
    'xml': 'application/xml',

    'pdf': "application/pdf",
    'txt': 'text/plain',

    'epub': "application/epub+zip",
    'booki': "application/x-booki+zip",

    None: 'application/octet-stream',
}

#Metadata construction routines










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

    def add_to_package(self, ID, fn, blob, mediatype=None):
        """Add an item to the zip, and save it in the manifest.  If
        mediatype is not provided, it will be guessed according to the
        extrension."""
        self.write_blob(fn, blob)
        if mediatype is None:
            ext = fn[fn.rfind('.') + 1:]
            mediatype = MEDIATYPES.get(ext, MEDIATYPES[None])
        self.manifest[ID] = (fn, mediatype)

    def _close(self):
        self.zipfile.close()

    def finish(self):
        """Finalise the metadata and write to disk"""
        self.info['manifest'] = self.manifest
        infojson = json.dumps(self.info, indent=2)
        self.add_to_package('info.json', 'info.json', infojson, 'application/json')
        self._close()

