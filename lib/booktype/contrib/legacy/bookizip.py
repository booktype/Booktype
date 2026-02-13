import os
import sys
import json

from zipfile import (ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED)


class BookiZip:
    def __init__(self, filename):
        self.zipfile = ZipFile(filename, 'r', ZIP_DEFLATED, allowZip64=True)
        self.info = None

    def read(self, filename):
        return self.zipfile.read(filename)

    def get_info(self):
        if not self.info:
            self.info = json.loads(self.zipfile.read('info.json'))

        return self.info

    def get_toc(self):
        info = self.get_info()
        toc = []

        def _get_section(sec):
            return [(0, elem['url'], elem['title']) for elem in sec]

        for entry in info['TOC']:
            if entry['type'] == 'booki-section':
                toc.append((1, entry['url'], entry['title']))

                toc += _get_section(entry['children'])
            else:
                toc.append((0, entry['url'], entry['title']))

        return toc

    def get_chapters(self):
        info = self.get_info()

        chapters = []

        for key, value in info['manifest'].items():
            if value['mimetype'] in ['text/html', 'application/xhtml+xml']:
                chapters.append(value['url'])

        return chapters

    def get_attachments(self):
        info = self.get_info()

        chapters = []

        for key, value in info['manifest'].items():
            if value['mimetype'] in ['image/png', 'image/jpeg', 'image/gif', 'image/tiff']:
                chapters.append(value['url'])

        return chapters


    def close(self):
        self.zipfile.close()