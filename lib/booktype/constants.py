# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

# Should track changes be turned on for the book
BOOK_TRACK_CHANGES = False

# PUBLISHING RELATED
PUBLISH_OPTIONS = ['mpdf', 'screenpdf', 'epub', 'mobi', 'xhtml']

# MOBI CONVERSION RELATED

# Options are "kindlegen" or "calibre"
MOBI_CONVERT = "calibre"
KINDLEGEN_PATH = "kindlegen"
CALIBRE_PATH = "ebook-convert"
CALIBRE_ARGS = ""

OBJAVI_URL = "http://objavi.booktype.pro/objavi.cgi"
ESPRI_URL = "http://objavi.booktype.pro/espri.cgi"

THIS_BOOKI_SERVER = os.environ.get('HTTP_HOST',
                                   'booktype-demo.sourcefabric.org')
CREATE_BOOK_VISIBLE = True
CREATE_BOOK_LICENSE = ""

FREE_REGISTRATION = True
ADMIN_CREATE_BOOKS = False
ADMIN_IMPORT_BOOKS = False

BOOKTYPE_MAX_USERS = 0
BOOKTYPE_MAX_BOOKS = 0
BOOKTYPE_BOOKS_PER_USER = -1

MAX_ADDITIONAL_METADATA = 3

BOOKTYPE_THEME_PLUGINS = {
  'custom': 'booktype.apps.themes.convert.custom',
  'academic': 'booktype.apps.themes.convert.academic'
}

EXPORT_WAIT_FOR = 90

EXPORT_SETTINGS = {
    'mpdf': [{u'name': u'size', u'value': u'A4'}, {u'name': u'custom_width', u'value': u''},
        {u'name': u'custom_height', u'value': u''}, {u'name': u'top_margin', u'value': u'20'},
        {u'name': u'side_margin', u'value': u'20'}, {u'name': u'bottom_margin', u'value': u'20'},
        {u'name': u'gutter', u'value': u'20'}, {u'name': u'show_header', u'value': u'on'},
        {u'name': u'header_margin', u'value': u'10'}, {u'name': u'show_footer', u'value': u'on'},
        {u'name': u'footer_margin', u'value': u'10'}, {u'name': u'bleed_size', u'value': u''},
        {u'name': u'styling', u'value': u''}, {u'name': u'crop_marks', u'value': u'off'}],
    'screenpdf': [{u'name': u'size', u'value': u'A4'}, {u'name': u'custom_width', u'value': u''},
        {u'name': u'custom_height', u'value': u''}, {u'name': u'top_margin', u'value': u'20'},
        {u'name': u'side_margin', u'value': u'20'}, {u'name': u'bottom_margin', u'value': u'20'},
        {u'name': u'gutter', u'value': u'20'}, {u'name': u'show_header', u'value': u'on'},
        {u'name': u'header_margin', u'value': u'10'}, {u'name': u'show_footer', u'value': u'on'},
        {u'name': u'footer_margin', u'value': u'10'}, {u'name': u'cover_image', u'value': u' '},
        {u'name': u'styling', u'value': u''}],
    'epub': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'mobi': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'xhtml': [{u'name': u'styling', u'value': u''}]
}

INCH_TO_MM = 25.4

PAGE_SIZE_DATA = {
    'comicbook':      (6.625 * INCH_TO_MM, 10.25 * INCH_TO_MM),
    "pocket":         (4.25 * INCH_TO_MM, 6.875 * INCH_TO_MM),
    "usletter":       (8.5 * INCH_TO_MM, 11 * INCH_TO_MM),
    "ustrade6x9":     (6 * INCH_TO_MM, 9 * INCH_TO_MM),
    "ustrade":        (6 * INCH_TO_MM, 9 * INCH_TO_MM),
    "landscape9x7":   (9 * INCH_TO_MM, 7 * INCH_TO_MM),
    "square7.5":      (7.5 * INCH_TO_MM, 7.5 * INCH_TO_MM),
    "royal":          (6.139 * INCH_TO_MM, 9.21 * INCH_TO_MM),
    "crownquarto":    (7.444 * INCH_TO_MM, 9.681 * INCH_TO_MM),
    "square8.5":      (8.5 * INCH_TO_MM, 8.5 * INCH_TO_MM),
    "us5.5x8.5":      (5.5 * INCH_TO_MM, 8.5 * INCH_TO_MM),
    "digest":         (5.5 * INCH_TO_MM, 8.5 * INCH_TO_MM),
    "us5x8":          (5 * INCH_TO_MM, 8 * INCH_TO_MM),
    "us7x10":         (7 * INCH_TO_MM, 10 * INCH_TO_MM),
    "a5":             (148, 210),
    "a4":             (210, 297),
    "a3 (nz tabloid)": (297, 420),
    "a2 (nz broadsheet)": (420, 594),
    "a1":             (594, 841),
    "b5":             (176, 250),
    "b4":             (250, 353),
    "b3":             (353, 500),
    "b2":             (500, 707),
    "b1":             (707, 1000),

    # Not so sure about next 3
    "uk tabloid":     (11 * INCH_TO_MM, 17 * INCH_TO_MM),
    "uk broadsheet":  (18 * INCH_TO_MM, 24 * INCH_TO_MM),
    "us broadsheet":  (15 * INCH_TO_MM, 22.75 * INCH_TO_MM),

    "berliner"     :  (315, 470),
    "foolscap (f4)":  (210, 330),
    "oamaru broadsheet" :(382, 540),
    "oamaru tabloid": (265, 380),
}


# These are default options for CSS settings

BOOKTYPE_CSS_BOOK = ('.objavi-chapter{ color: #000; }'
                     'a { text-decoration:none; color:#000; } '
                     'h1 .initial{ color: #000; } '
                     '.objavi-subsection{ display: block; '
                     'page-break-before: always; '
                     '/* page-break-after: always;*/ '
                     'text-transform: uppercase; font-size: 20pt; }'
                     'body .objavi-subsection:first-child{ '
                     'page-break-before: avoid; } '
                     '.objavi-subsection .initial { '
                     'font-size: 1em; color: #000; }'
                     '.objavi-subsection-heading { font-size: 20pt; '
                     'text-align: center; '
                     'line-height: 300px; font-weight: normal; } '
                     'h1 { page-break-before: always; } '
                     'table { float: none; }'
                     'h1.frontpage{ page-break-after:always; margin-top:70%; '
                     'font-size: 20pt; '
                     'text-align: center; page-break-before: avoid; '
                     'font-weight: normal; }'
                     'div.copyright{ padding: 1em; } '
                     '/* TOC ******************************/ '
                     'table { float: none; } '
                     'table.toc { font-size: 1.1em; width: 95%; } '
                     'table.toc td{ vertical-align:top padding-left: 0.5em; } '
                     'td.chapter { padding: 0 0.5em; text-align: right; } '
                     'table.toc td.pagenumber { text-align: right; '
                     'vertical-align:bottom; } '
                     'td.section { padding-top: 1.1em; font-weight: bold; } '
                     '/* End TOC **************************/ '
                     'pre { overflow: hidden; white-space: pre-wrap; } '
                     'h1 h2 h3 h4 h5 h6{ page-break-after: avoid; '
                     'page-break-inside: avoid; } '
                     '.page-break{ page-break-before: always; height: 7em; '
                     'display: block; } '
                     '#right-footer { text-align: right; } '
                     '#left-footer { text-align: left; } '
                     'a { word-wrap: break-word; } '
                     '.objavi-no-page-break { page-break-inside: avoid; } '
                     '.unseen{ z-index: -66; margin-left: -1000pt; }'
                     'sup {vertical-align:text-top;font-size:0.7em; }'
                     'img { max-width: 95%; }'
                     'p { word-wrap: break-word; }'
                     'li { word-wrap: break-word; }'
                     '#InsertNote_NoteList { word-wrap: break-word; }')

BOOKTYPE_CSS_BOOKJS = ('/* DOCUMENT */ @page { size: auto;}'
                       'body { word-break: break-word; -webkit-hyphens: auto;'
                       'hyphens: auto; font-family: "Liberation Serif";'
                       'background-color: white;}' '/* CONTENT */'
                       'img { max-width: 90%; height: auto;'
                       'image-resolution: from-image;}'
                       'sup  { font-size: 80%;}'
                       'p { line-height: 130%; word-break: break-word;'
                       '/* text-align: justify; */'
                       'text-align: left;}'
                       'a { color: #000; text-decoration: none; '
                       'word-wrap: break-word;}'
                       'ol ul { text-align: justify;}'
                       'li { margin-left: 1em; word-wrap: break-word; '
                       'page-break-inside: avoid; windows: 4; orphans: 4;}'
                       '/* HEADINGS */'
                       'h1 {}'
                       'h1 .initial { display: none;}'
                       'h1 .subtitle {}'
                       'h1 .author { display: block; margin-top: 0.2in; '
                       'font-weight: normal;}'
                       'h1 .comma { font-size: 22pt; display: none;}'
                       'h2 { page-break-after: avoid;}'
                       'h3 { page-break-after: avoid;}'
                       'h4 { page-break-after: avoid;}'
                       'h5 { font-weight: normal; text-align: left;'
                       'page-break-after: avoid;}'
                       '/* CODE BLOCKS */'
                       'pre { white-space: pre-wrap; /* css-3 */ '
                       'white-space: -moz-pre-wrap;  /* Mozilla since 1999 */'
                       'white-space: -pre-wrap;/* Opera 4-6 */'
                       'white-space: -o-pre-wrap; /* Opera 7 */'
                       'word-wrap: break-word; /* Internet Explorer 5.5+ */'
                       'widows:4; orphans:4;}'
                       'code {}'
                       '/* TOC */'
                       '#pagination-toc-title { font-size: 20pt; '
                       'font-weight: 700; text-align: left; '
                       'padding-bottom: .4in;}'
                       '.pagination-toc-entry {/* width: 6.2in; */ '
                       'width: 90%; display: block; padding-bottom: .3in; '
                       'font-size: 16pt;}'
                       '.pagination-toc-entry .pagination-toc-pagenumber { '
                       'font-weight: 400; display: inline-block; '
                       'vertical-align: text-bottom; font-size: 16pt; '
                       'float:right; '
                       '/* SET AUTOMATICALLY */}'
                       '.pagination-toc-entry.section { font-weight:700; '
                       'font-size: 16pt; text-transform: uppercase; '
                       'padding-bottom: .3in;}'
                       '/* FRONT MATTER */'
                       '#booktitle { margin-top: 1.7in; font-size: 26pt; '
                       'font-weight: normal; text-align: center; '
                       'text-transform: uppercase;}'
                       '#booksubtitle { font-size: 22px; margin-top: 0.2in; '
                       'font-weight: normal; text-align: center;}'
                       '#bookeditors { padding-top: 1.5in; '
                       'font-weight: normal; text-align: center; '
                       'font-size: 24pt;}'
                       '#bookpress { padding-top: 1.8in; font-weight: normal;'
                       'text-align: center; font-size: 24pt;}'
                       '#copyrightpage { font-weight: normal; '
                       'font-size: 18pt; padding-top: 0.2in;}'
                       '/* HEADER */'
                       '.pagination-header {font-size: 12pt;'
                       'font-weight: light;}'
                       '.pagination-pagenumber {font-size: 12pt;}'
                       '.pagination-header '
                       '.pagination-section { display: none; }'
                       '.pagination-toc-text .initial { display: none; }'
                       '.pagination-chapter .initial { display: none; }'
                       '/* MISC */'
                       '.imagecaption { font-size: 9pt; padding-left: 0.2in;'
                       'line-height: 18px; text-align: justify;'
                       'font-weight: normal; display: block;}'
                       '.pagebreak { -webkit-region-break-after: always;}'
                       '.pagebreakbefore{'
                       ' -webkit-region-break-before: always;}'
                       '.objavi-chapter .initial { display: none;}'
                       '.objavi-subsection { display: none;}'
                       '.objavi-subsection-heading { '
                       'line-height: 120px !important; '
                       '/* work-around to make section title pages no longer '
                       'than one page */ font-size: 22px; font-weight: bold;'
                       ' text-align: left; display: none;}'
                       '@media screen { .page {  border: solid 1px #000;'
                       '  margin-bottom: .2in; }'
                       'body {	background-color: #efefef; }}'
                       '#InsertNote_NoteList { word-wrap: break-word;}')


BOOKTYPE_CSS_EBOOK = ('.objavi-chapter{  color: #000;  display:none;} '
                      'a {  text-decoration:none;  color:#000;} '
                      'h1 .initial{  color: #000;  display:none;} '
                      '.objavi-subsection{  display: block; '
                      'page-break-before: always;} '
                      'body .objavi-subsection:first-child{ '
                      'page-break-before: avoid;} '
                      '.objavi-subsection .initial { color: #000; '
                      'display:none;} .objavi-subsection-heading {'
                      'font-size: 20pt;  text-align: center;  '
                      'line-height: 300px;  font-weight: normal;}'
                      'table {  float: none;} h1.frontpage{'
                      'page-break-after:always;  margin-top:70%; '
                      'font-size: 20pt;  text-align: center;'
                      'page-break-before: avoid;  max-width: 700pt;  '
                      'font-weight: normal;} div.copyright{padding: 1em;}'
                      '/* TOC ******************************/'
                      'table {  float: none;}'
                      'table.toc { font-size: 1.1em;  width: 95%;}'
                      'table.toc td{ vertical-align:top; padding-left: 0.5em;}'
                      'td.chapter { padding: 0 0.5em;  text-align: right;} '
                      'table.toc td.pagenumber { text-align: right;  '
                      'vertical-align:bottom;} '
                      'td.section {  padding-top: 1.1em;  font-weight: bold;}'
                      '/* End TOC **************************/ '
                      'img { max-width: 500px; height: auto;}'
                      '.objavi-no-page-break {page-break-inside: avoid;} '
                      '.unseen { z-index: -66; margin-left: -1000pt;} '
                      '.objavi-subsection-heading{  height:860px; '
                      'font-size:0px;  display:block;}')

BOOKTYPE_CSS_PDF = ('.objavi-subsection{ display: block; '
                    'page-break-before: always; /* page-break-after: always;*/'
                    'text-transform: uppercase; font-size: 20pt; } '
                    'body .objavi-subsection:first-child{ '
                    'page-break-before: avoid; } '
                    '.objavi-subsection .initial { font-size: 1em;'
                    'color: #000; } .objavi-subsection-heading {'
                    'font-size: 20pt; text-align: center; line-height: 300px;'
                    'font-weight: normal;} h1 { page-break-before: always; } '
                    'table { float: none; } '
                    'h1.frontpage{ page-break-after:always; margin-top:70%; '
                    'font-size: 20pt; text-align: center; '
                    'page-break-before: avoid; font-weight: normal; } '
                    'div.copyright{ padding: 1em; } '
                    '/* TOC ******************************/ '
                    'table { float: none; } '
                    'table.toc { font-size: 1.1em; width: 95%; } '
                    'table.toc td{ vertical-align:top; padding-left: 0.5em; } '
                    'td.chapter { padding: 0 0.5em; text-align: right; } '
                    'table.toc td.pagenumber { text-align: right; '
                    'vertical-align:bottom; } td.section { padding-top: 1.1em;'
                    'font-weight: bold; } '
                    '/* End TOC **************************/ '
                    'pre { overflow: hidden; white-space: pre-wrap; } '
                    'h1, h2, h3, h4, h5, h6{   page-break-after: avoid; '
                    'page-break-inside: avoid; } '
                    '.page-break{ page-break-before: always; height: 7em;'
                    'display: block; } a { word-wrap: break-word; } '
                    '.objavi-no-page-break { page-break-inside: avoid; } '
                    '/*To force a blank page it is sometimes necessary to '
                    'add unseen  content. Display:none and visibility: hidden'
                    ' do not work -- the  renderer realises that they are not '
                    'there and skips the page. So we  add a tiny bit of text '
                    'beyond the margin of the page. */ '
                    '.unseen{ z-index: -66; margin-left: -1000pt; }'
                    'img { max-width: 95%; } p { word-wrap: break-word; }'
                    'li { word-wrap: break-word; }'
                    '#InsertNote_NoteList { word-wrap: break-word; } ')

BOOKTYPE_CSS_ODT = ('body {} #book-title { font-size: 64pt; '
                    'page-break-before: avoid; margin-bottom: 12em; '
                    'max-width: 700px;} .unseen { display: none;}'
                    '.chapter { color: #000;} h1 .initial { color: #000; '
                    'font-size: 2em;} body .subsection:first-child {} '
                    'h1 { page-break-before: always;} '
                    '.objavi-subsection{ text-transform: uppercase; '
                    'font-size: 20pt;} .objavi-subsection .initial { '
                    'font-size: 1em; color: #000;}'
                    '.objavi-subsection-heading{ font-size: 36pt; '
                    'font-weight: bold; page-break-before: always;} '
                    'table { float: none;} h1.frontpage{ font-size: 64pt; '
                    'text-align: center; max-width: 700px;} '
                    'div.copyright{ padding: 1em;} pre { max-width:700px; '
                    'overflow: hidden;} '
                    'img { max-width: 700px; height: auto;}')
