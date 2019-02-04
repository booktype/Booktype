# -*- coding: utf-8 -*-
from booktype.utils import config

IMAGES_DIR = 'Images'
STYLES_DIR = 'Styles'
FONTS_DIR = 'Fonts'
DOCUMENTS_DIR = 'Text'
DEFAULT_LANG = 'en'
DEFAULT_DIRECTION = 'ltr'

EPUB_VALID_IMG_ATTRS = frozenset([
    "alt", "class", "dir", "height", "id", "ismap", "longdesc",
    "style", "title", "usemap", "width", "xml:lang", "src", "transform-data"
])

EPUB_DOCUMENT_WIDTH = config.get_configuration('EPUB_DOCUMENT_WIDTH')
EPUB_NOT_ALLOWED_TAGS = config.get_configuration('EPUB_NOT_ALLOWED_TAGS')
EPUB_ALLOWED_TAG_ATTRS = config.get_configuration('EPUB_ALLOWED_TAG_ATTRS')
EPUB_AVAILABLE_INBODY_ROOT_TAGS = config.get_configuration('EPUB_AVAILABLE_INBODY_ROOT_TAGS')
