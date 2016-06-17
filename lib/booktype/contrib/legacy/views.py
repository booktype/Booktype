# This file is part of Booktype.
# Copyright (c) 2015 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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
import tempfile
import datetime
import json
import uuid
import celery
import sputnik
import time
import requests
import logging
import urlparse

from StringIO import StringIO
from collections import OrderedDict

from django.views.generic.base import View
from django.http import HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.conf import settings

from ebooklib import epub
from ebooklib.plugins import standard
from ebooklib.utils import parse_html_string
from lxml import etree

from booktype.apps.export.epub import ExportEpubBook

from booktype.apps.loadsave.utils import RestrictExport
from booktype.utils import download, config
from booktype.utils.misc import TidyPlugin
from .bookizip import BookiZip


logger = logging.getLogger('booktype.legacy')


def export_book(input_file, filename):
    """Reads content of book in Booki.zip format and converts it to EPUB format.

    This function reads content of the book in Booki.zip file, creates new
    book in EPUB format and converts entire content into it. There are some
    things which are different in new EPUB format. One of them is how links 
    and interlinks are handled.
    """

    epub_book = ExportEpubBook()

    # Creating new EPUB file
    epub_book.add_prefix('bkterms', 'http://booktype.org/')

    # Read old Booki.zip format
    bookizip = BookiZip(input_file)

    _toc, _section, _section_name = [], [], None
    spine = ['nav']

    # Get filesnames of all the chapters/sections
    file_names = [file_name[6:-5] for _, file_name, _ in bookizip.get_toc()]

    x = 0
    for typ, file_name, title in bookizip.get_toc():
        # Ignore sections
        if typ == 1:
            if _section_name is None and len(_section) > 0:
                _toc.append(_section)
            elif len(_section) > 0:
                _toc.append((epub.Section(_section_name), _section[:]))

            _section_name = title
            _section = []
            continue

        # Create new chapter with new filename
        c1 = epub.EpubHtml(
            title=title,
            file_name='{}.xhtml'.format(file_name[6:-5])
        )
        cont = unicode(bookizip.read(file_name), 'utf-8')
        _section.append(c1)

        try:
            tree = parse_html_string(cont.encode('utf-8'))
        except:
            # Just ignore everything if we can not parse the chapter
            continue

        # Change all the links in the document
        for elem in tree.iter():
            if elem.tag == 'a':
                href = elem.get('href')

                if href:
                    urlp = urlparse.urlparse(href)
                    url_title = urlp.path

                    if urlp.scheme == '':
                        if url_title and url_title in file_names:
                            fixed_href = url_title + '.xhtml'
                            if urlp.fragment:
                                fixed_href = "{}#{}".format(fixed_href, urlp.fragment)

                            elem.set('href', fixed_href)
                        else:
                            # ovdje brishe sve shto je externo. to se ne bi trebalo desavati
                            elem.drop_tag()

            c1.content = etree.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)

        epub_book.add_item(c1)
        spine.append(c1)
        x += 1

    if _section_name is None and len(_section) > 0:
        _toc.append(_section)
    elif len(_section) > 0:
        _toc.append((epub.Section(_section_name), _section[:]))

    # Add all of the attachments
    for att_name in bookizip.get_attachments():
        try:
            blob = bookizip.read(att_name)
        except (IOError, OSError):
            continue
        else:
            itm = epub.EpubImage()
            itm.file_name = att_name
            itm.content = blob
            epub_book.add_item(itm)

    epub_book.set_title('Title', 'main')
    epub_book.set_language('en')
    epub_book.add_author('Author', role='aut', uid='author')

    epub_book.toc = _toc
    epub_book.spine = spine

    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())

    opts = {'plugins': [TidyPlugin(), standard.SyntaxPlugin()]}
    epub.write_epub(filename, epub_book, opts)



def download_bookizip(base_path, url_path):

    r = requests.get(url_path, verify=config.get_configuration('REQUESTS_VERIFY_SSL_CERT'))

    try:
        f = open('{}/booki.zip'.format(base_path), 'wb')
        f.write(StringIO(r.content).read())
        f.close()
    except Exception:
        logger.exception('Could not save booki.zip file')


def send_request(book_url, conf, request):
    data = {
        "assets": {
            "input.epub": book_url
        },
        "input": "input.epub",
        "outputs": {}
    }
    mpdf_settings = {}

    _ext = 'pdf'
    if conf['format'] == 'epub':
        _ext = 'epub'

    if conf['format'] == 'mobi':
        _ext = 'mobi'

    _css = request.POST.get('css', '')
    tag = '/* CUSTOM */'

    if _css.find(tag) != -1:
        _css = _css[_css.find(tag):]
    else:
        _css = ''

    if conf['format'] == 'mpdf':
        mpdf_settings = {
            'size': request.POST.get('booksize', 'A4'),
            'custom_width': request.POST.get('custom_width', 0),
            'custom_height': request.POST.get('custom_height', 0),
            'side_margin': request.POST.get('side_margin', 0),
            'bottom_margin': request.POST.get('bottom_margin', 0),
            'top_margin': request.POST.get('top_margin', 0),
            'gutter': request.POST.get('gutter', 0),
            'show_header': 'on',
            'header_margin': 5,
            'show_footer': 'on',
            'footer_margin': 5,
            'bleed_size': 0,
            'styling': _css,
            'crop_marks': 'off'
        }

    if conf['format'] == 'screenpdf':
        mpdf_settings = {
            'size': request.POST.get('booksize', 'A4'),
            'custom_width': request.POST.get('custom_width', 0),
            'custom_height': request.POST.get('custom_height', 0),
            'side_margin': request.POST.get('side_margin', 0),
            'bottom_margin': request.POST.get('bottom_margin', 0),
            'top_margin': request.POST.get('top_margin', 0),
            'gutter': request.POST.get('gutter', 0),
            'show_header': 'on',
            'header_margin': 5,
            'show_footer': 'on',
            'footer_margin': 5,
            'bleed_size': 0,
            'styling': _css,
            'crop_marks': 'off'
        }

    data["outputs"][conf['format']] = {
        "profile": conf['format'],
        "config": {
            "project_id": conf['title'],
            "settings": mpdf_settings,
            "theme": {}
        },
        "output": "{}.{}".format(conf['title'], _ext)
    }

    if 'cover_url' in request.POST:
        if conf['format'] == 'screenpdf':
            data['assets']['screenpdf_cover_image'] = request.POST.get('cover_url', '')
            data['outputs'][conf['format']]['config']['cover_image'] = 'screenpdf_cover_image'
        elif conf['format'] == 'epub':
            data['assets']['epub_cover_image'] = request.POST.get('cover_url', '')
            data['outputs'][conf['format']]['config']['cover_image'] = 'epub_cover_image'
        elif conf['format'] == 'mobi':
            data['assets']['mobi_cover_image'] = request.POST.get('cover_url', '')
            data['outputs'][conf['format']]['config']['cover_image'] = 'mobi_cover_image'        

    output_results = {}

    convert_url = '{}/_convert/'.format(settings.CONVERT_URL)
    result = download.fetch_url(convert_url, data, method='POST')

    if not result:
        return None

    task_id = result['task_id']
    start_time = time.time()

    while True:
        if time.time() - start_time > 60 * 8:
            break

        dta = download.fetch_url(settings.CONVERT_URL, task_id, {}, 'GET')

        if not dta:
            dta = {'state': ''}
            logger.exception('Could not read response data.')

        if dta['state'] == 'SUCCESS':
            for _key in data["outputs"].iterkeys():
                if 'state' in dta['result'][_key]:
                    if dta['result'][_key]['state'] == 'SUCCESS':
                        output_results[_key] = True
                    elif dta['result'][_key]['state'] == 'FAILURE':
                        output_results[_key] = False

            if len(output_results) == len(data["outputs"].keys()):
                def _x(_key):
                    d = {}
                    if 'result' in dta['result'][_key]:
                        d = dta['result'][_key]['result']
                    d['status'] = output_results[_key]
                    return d

                urls = {_key: _x(_key) for _key in output_results.iterkeys()}

                _now = datetime.datetime.now()

                _files = {}

                for output_type, result in dta['result'].iteritems():
                    if 'state' in result:
                        if result['state'] == 'SUCCESS':
                            return result
                        else:
                            logger.error('Some kind of error in publishing.')
                break

        if dta['state'] == 'FAILURE':
            logger.error('Some kind of error in publishing.')
            break

    return None


class ConvertView(RestrictExport, View):
    """Convert view for faking Objavi call.

    Booktype 1.6 will call this URL thinking it is talking with Objavi service. This view will
    parse all the arguments and then send request to the new Booktype 2.0 convert scripts. 

    It will also download book from Booktype 1.6 system in Booki.zip file. File will be saved
    into temporary file. During our call to Booktype 2.0 system we will use unique id for
    referencing our downloaded book. For that we will use custom build URL which will be
    served by ConvertResourceView.
    """

    def post(self, request):
        token = str(uuid.uuid1())

        # sandbox directory for this request
        base_path = os.path.join(settings.MEDIA_ROOT, "bookizip", token)
        os.makedirs(base_path)

        bk_server = request.POST['server']
        bk_book = request.POST['book']

        logger.debug('Downloading http://{}/export/{}/export/'.format(bk_server, bk_book))

        download_bookizip(base_path,
                          'http://{}/export/{}/export/'.format(bk_server, bk_book))

        book_url = '{}{}'.format(settings.BOOKTYPE_URL, reverse('legacy:convert_resource', args=[token]))

        _format = {
            'book': 'mpdf',
            'web': 'screenpdf',
            'epub': 'epub'}.get(request.POST.get('mode', 'book'))

        output_format = request.POST.get('output_format', None)
        if output_format == 'mobi':
            _format = 'mobi'

        conf = {
            'format': _format,
            'title': bk_book
        }

        logger.debug('Requesting %s export for %s book.', _format, book_url)

        result = send_request(book_url, conf, request)

        if result is None:
            logger.error('Some kind of error while communicating with Conversion scripts.')
            return HttpResponse('', content_type="text/plain")

        # Return result in old Booktype 1.6 format
        response_data = "{}\n{}".format(result['result']['output'], result['result']['output'])

        return HttpResponse(response_data, content_type="text/plain")


class ConvertResourceView(RestrictExport, View):
    """View for returning EPUB content of the Booktype 1.6 book.

    New convert scripts will use this URL to fetch content of the book as EPUB file. We will parse the
    book in Booki.zip file, convert it into EPUB and return content of that newly created file.
    """

    def get(self, request, resource_id):
        response = HttpResponse(content_type='application/epub+zip')
        response['Content-Disposition'] = 'attachment; filename=bookizip.epub'

        temp_dir = tempfile.mkdtemp()
        filename = '%s/export.epub' % temp_dir

        input_file = os.path.join(settings.MEDIA_ROOT, "bookizip", resource_id, 'booki.zip')
        export_book(input_file, filename)

        response.write(open(filename, 'rb').read())

        os.unlink(filename)
        os.rmdir(temp_dir)

        return response
