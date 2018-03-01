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
from django.utils.translation import ugettext_noop

# SSL cert verification during request using 'requests' lib
REQUESTS_VERIFY_SSL_CERT = True

# SECURITY CLASS
BOOKTYPE_BASE_SECURITY_CLASS = 'booktype.utils.security.base.BaseSecurity'

# Should track changes be turned on for the book
BOOK_TRACK_CHANGES = False

# CHAPTER STATUS RELATED
CHAPTER_STATUS_LIST = [
    {'name': ugettext_noop('new'), 'color': '#3a87ad'},
    {'name': ugettext_noop('needs content'), 'color': '#ff0000'},
    {'name': ugettext_noop('completed'), 'color': '#5cb85c'},
    {'name': ugettext_noop('to be proofed'), 'color': '#f0ad4e'}
]

CHAPTER_STATUS_DEFAULT = CHAPTER_STATUS_LIST[0]['name']

# IMPORTERS RELATED STUFF
BOOKTYPE_IMPORTERS = {
    'epub': ('booktype.importer.epub', 'import_epub'),
    'docx': ('booktype.importer.docx', 'import_docx')
}


# Default styles matched so far. We'll add more in future
# these constants are used on docimporter.py to correctly
# assign classes to imported elements
DOCX_PARAGRAPH_STYLES_MAP = {
    'AuthorName': 'authorname',
    'Reference': 'reference',
    'Citation': 'bk-cite'
}

# Which elements are considered <h1> style
H1_STYLES = ['title', 'heading1']

# Which elements are considered <h2> style
H2_STYLES = ['heading2']

# Which elements are considered <h3> style
H3_STYLES = ['heading3']

# Which elements are considered <h4> style
H4_STYLES = ['heading4']

# Which elements are considered <h5> style
H5_STYLES = ['heading5']

# Which elements are considered <h6> style
H6_STYLES = ['heading6']

# All of our Heading styles
DOCX_HEADING_STYLES = H1_STYLES + H2_STYLES + H3_STYLES + H4_STYLES + H5_STYLES + H6_STYLES

DOCX_HEADING_STYLES_TUPLE = (
    ('h1', H1_STYLES),
    ('h2', H2_STYLES),
    ('h3', H3_STYLES),
    ('h4', H4_STYLES),
    ('h5', H5_STYLES),
    ('h6', H6_STYLES)
)

# This will allow settings custom class on clients
DOCX_IMPORTER_CLASS = 'booktype.importer.WordImporter'

# possible options: "overwrite", "append"
UPLOAD_DOCX_DEFAULT_MODE = None

# END IMPORTERS STUFF

# SERVER RELATED
THIS_BOOKI_SERVER = os.environ.get('HTTP_HOST', 'booktype-demo.sourcefabric.org')

# ADMINISTRATIVE RELATED
CREATE_BOOK_VISIBLE = False
CREATE_BOOK_LICENSE = ""
CREATE_BOOK_LANGUAGE = "en"

FREE_REGISTRATION = True
ADMIN_CREATE_BOOKS = False
ADMIN_IMPORT_BOOKS = False

BOOKTYPE_MAX_USERS = 0
BOOKTYPE_MAX_BOOKS = 0
BOOKTYPE_BOOKS_PER_USER = {
    # -1 means no limits
    'limit_global': -1,
    'limit_by_user': [
        # example
        # {
        #     'username': 'john',
        #     'limit': 3,
        # }
    ]
}

GROUP_LIST_PAGE_SIZE = 20
USER_LIST_PAGE_SIZE = 20
BOOK_LIST_PAGE_SIZE = 20

# google analytics
USE_GOOGLE_ANALYTICS = False
GOOGLE_ANALYTICS_ID = ''

# reports
REPORTS_EMAIL_FROM = 'booktype@booktype.pro'
REPORTS_EMAIL_USERS = ['booktype@booktype.pro']
REPORTS_CUSTOM_FONT_PATH = False

MAX_ADDITIONAL_METADATA = 3

# IMPORT RELATED
EPUB_COVER_MIN_DPI = 300
EPUB_COVER_MIN_SIZE = 500
EPUB_COVER_MAX_SIZE = 2800
EPUB_COVER_MAX_PIXELS = 3200000

# PUBLISHING RELATED
PUBLISH_OPTIONS = ['mpdf', 'screenpdf', 'epub3', 'epub2', 'icml', 'docx', 'mobi', 'xhtml']

# mobi conversion
# Options are "kindlegen" or "calibre"
MOBI_CONVERT = "calibre"
KINDLEGEN_PATH = "kindlegen"
CALIBRE_PATH = "ebook-convert"
CALIBRE_ARGS = ""

OBJAVI_URL = "http://objavi.booktype.pro/objavi.cgi"
ESPRI_URL = "http://objavi.booktype.pro/espri.cgi"

# theme plugins
BOOKTYPE_THEME_PLUGINS = {
    'custom': 'booktype.apps.themes.convert.custom',
    'academic': 'booktype.apps.themes.convert.academic'
}

# define path to module where class ExportBook is located
BOOKTYPE_EXPORT_CLASS_MODULE = 'booktype.apps.export.utils'

EXPORT_WAIT_FOR = 90

# convert constants
CONVERT_EDITOR_WIDTH = 898
XHTML_DOCUMENT_WIDTH = 2480
MOBI_DOCUMENT_WIDTH = 1500
EPUB_DOCUMENT_WIDTH = 1500

# editor stuff here
EDITOR_AUTOSAVE_ENABLED = False  # disabled by default
EDITOR_AUTOSAVE_DELAY = 60  # time in seconds
EDITOR_SETTINGS_ROLES_SHOW_PERMISSIONS = 0

# end editor stuff

EPUB_NOT_ALLOWED_TAGS = (
    # 'strip' - drop tag, leave content
    # 'drop' - drop tag, drop content
    # 'replace' - replace tag with 'replacement'
    # EXAMPLES:
    # {'tag': 'i', 'action': 'strip'},
    # {'tag': 'b', 'action': 'drop'},
    # {
    #     'tag': 'u',
    #     'action': 'replace',
    #     'replacement': {
    #         'tag': 'span',
    #         'attrs': (
    #             ('style', 'text-decoration: underline;'),
    #             ('class', 'happy'),
    #         )
    #     }
    # },
)

# According to epubcheck, after(inside) body tag,
# on the 1st level of deepness, must be only the next list of tags.
# If tag doesn't fit requierements, it will be replaced with "<p>"
EPUB_AVAILABLE_INBODY_ROOT_TAGS = (
    'address', 'blockquote', 'del', 'div', 'dl', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'ins', 'noscript', 'ns:svg', 'ol', 'p', 'pre', 'script', 'table', 'ul'
)

# mapping tag and allowed attributes in it
# required by epubcheck
EPUB_ALLOWED_TAG_ATTRS = (
    ('ol', ('class', 'dir', 'id', 'lang', 'style', 'title', 'xml:lang')),
)


XHTML_DEFAULT_STYLING = u'''
.group_img {
    page-break-inside: avoid;
    padding-top: 14.7pt;
    margin-bottom: 14.7pt;
    overflow: auto;
}
img {
  vertical-align: top;
  display: inline-block;
  max-width: 100%;
  height: auto;
  box-sizing: border-box;
}
.image-layout-1image_1caption_left img {
    float: right;
}
.image-layout-1image_1caption_right img {
    float: left;
}
.image-layout-2images_2captions_bottom div.wrap {
  display: inline-block;
  vertical-align: top;
}
caption,
.caption,
.caption_small,
.caption_table,
.caption_img,
.caption_fig,
.caption_image,
.caption_figure {
    font-family: "roboto";
    font-size: 9.45pt;
    /*line-height: 14.7pt; /**/
    text-align: left;
    font-style: italic;
    font-weight: normal;
    color: #000000;
}
div.caption_small {
  padding-top: 0;
  margin-top: 10px;
  display: block;
  box-sizing: border-box;
}
.image-layout-1image_1caption_right div.caption_small {
  display: inline-block;
  margin-top: 0;
  padding-left: 0.5em;
}
.image-layout-1image_1caption_left div.caption_small {
  display: inline-block;
  margin-top: 0;
  padding-right: 0.5em;
}
'''


# indicates if ContentCleanUpPlugin should be used or not
# this plugin is meant to remove all unnecessary and empty tags
ENABLE_CONTENT_CLEANUP_ON_EXPORT = False

# list of attributes that want to be removed from nodes in ContentCleanUpPlugin
ATTRS_TO_REMOVE_ON_CLEANUP = ['style']

# list of tags that are meant to be removed by the ContentCleanUpPlugin
TAGS_TO_REMOVE_ON_CLEANUP = ['br']

# list of tags that are supposed to be empty but are not remove in ContentCleanupPlugin
ALLOWED_EMPTY_TAGS = ['hr', 'img', 'link']

# list of css classes for nodes that can be empty given their behaviour e.g: .group_img, .bk-image-editor
ALLOWED_EMPTY_BY_CLASSES = ['group_img', 'group_table', 'bk-image-editor']

EXPORT_SETTINGS = {
    'mpdf': [
        {u'name': u'size', u'value': u'A4'}, {u'name': u'custom_width', u'value': u''},
        {u'name': u'custom_height', u'value': u''}, {u'name': u'top_margin', u'value': u'20'},
        {u'name': u'side_margin', u'value': u'20'}, {u'name': u'bottom_margin', u'value': u'20'},
        {u'name': u'gutter', u'value': u'20'}, {u'name': u'show_header', u'value': u'on'},
        {u'name': u'header_margin', u'value': u'10'}, {u'name': u'show_footer', u'value': u'on'},
        {u'name': u'footer_margin', u'value': u'10'}, {u'name': u'bleed_size', u'value': u''},
        {u'name': u'styling', u'value': u''},
        {u'name': u'crop_marks', u'value': u'off'}, {u'name': u'crop_margin', u'value': u'18'}],
    'screenpdf': [
        {u'name': u'size', u'value': u'A4'}, {u'name': u'custom_width', u'value': u''},
        {u'name': u'custom_height', u'value': u''}, {u'name': u'top_margin', u'value': u'20'},
        {u'name': u'side_margin', u'value': u'20'}, {u'name': u'bottom_margin', u'value': u'20'},
        {u'name': u'gutter', u'value': u'20'}, {u'name': u'show_header', u'value': u'on'},
        {u'name': u'header_margin', u'value': u'10'}, {u'name': u'show_footer', u'value': u'on'},
        {u'name': u'footer_margin', u'value': u'10'}, {u'name': u'cover_image', u'value': u' '},
        {u'name': u'styling', u'value': u''}],
    'epub2': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'epub3': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'icml': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'docx': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'mobi': [{u'name': u'cover_image', u'value': u' '}, {u'name': u'styling', u'value': u''}],
    'xhtml': [{u'name': u'styling', u'value': XHTML_DEFAULT_STYLING}]
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
