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
import logging

import ebooklib
import ebooklib.epub
import ebooklib.utils

from booktype.utils import config

__all__ = ("get_cover_image", )

logger = logging.getLogger("booktype.importer.epub")

# minimal DPI of the image (if specified)
MIN_DPI = config.get_configuration('EPUB_COVER_MIN_DPI')

# minimal size on the shorter axis (pixels)
MIN_SIZE = config.get_configuration('EPUB_COVER_MIN_SIZE')

# maximal size on the longer axis (pixels)
MAX_SIZE = config.get_configuration('EPUB_COVER_MAX_SIZE')

# maximum number of pixels (width * height)
MAX_PIXELS = config.get_configuration('EPUB_COVER_MAX_PIXELS')

# maximum size of image content
MAX_CONTENT_SIZE = MAX_PIXELS * 4


def get_cover_image(book):
    """
    Returns the book's cover image item, or None if none can be found.
    """

    cover_image_id = get_id_from_manifest(book) or get_id_from_metadata(book)

    if cover_image_id:
        return book.get_item_with_id(cover_image_id)

    cover_html = get_cover_html(book)

    if cover_html:
        image_name = get_image_name_from_html(cover_html)
        if image_name:
            return get_item_with_name(book, image_name)


def get_id_from_manifest(book):
    """ Returns the ID of the cover item from EPUB3 manifest.
    """
    return next((item.id for item in book.get_items() if type(item) == ebooklib.epub.EpubCover), None)


def get_id_from_metadata(book):
    """ Returns the ID of the cover item from EPUB2 style meta tag.
    """
    try:
        cover_meta = book.get_metadata("OPF", "cover")
        if cover_meta:
            return cover_meta[0][1]["content"]
    except:
        pass


def get_item_with_name(book, name):
    """
    Returns the item from the book that has the specified file name.
    """
    return next((item for item in book.get_items() if item.file_name == name), None)


def get_image_name_from_html(item):
    """
    Returns the name of the first image used inside the specified document item.
    """
    try:
        tree = ebooklib.utils.parse_string(item.get_content())
    except Exception as e:
        logger.error('epub:cover.py Error while trying to read item content')
        logger.exception(e)
        return None

    # continue parsing if not fail
    tree_root = tree.getroot()
    images = tree_root.xpath('//xhtml:img', namespaces={'xhtml': ebooklib.epub.NAMESPACES['XHTML']})

    if len(images) == 0:
        return None

    href = images[0].get("src")
    base = os.path.dirname(item.file_name)

    return os.path.normpath(os.path.join(base, href))


def get_cover_html(book):
    """ Returns the document item that is most likely the cover HTML document.
    """

    # item of type CoverHtml
    item = next((item.id for item in book.get_items() if type(item) == ebooklib.epub.EpubCoverHtml), None)
    if item:
        return item

    # item with type set to "cover" in OPF guide
    item_name = next((elem["href"] for elem in book.guide if elem["type"] == "cover"), None)
    if item_name:
        return get_item_with_name(book, item_name)

    # item with type set to "start" in OPF guide
    item_name = next((elem["href"] for elem in book.guide if elem["type"] == "start"), None)
    if item_name:
        return get_item_with_name(book, item_name)

    # last ditch
    return book.get_item_with_id("cover")


def is_valid_cover(item):
    from PIL import Image
    from StringIO import StringIO

    if item.media_type not in ebooklib.epub.IMAGE_MEDIA_TYPES:
        return False, "unsupporter media type: {}".format(item.media_type)

    content = item.get_content()

    if len(content) > MAX_CONTENT_SIZE:
        return False, "image content too big"

    image = Image.open(StringIO(content))

    dpi = image.info.get("dpi")
    width, height = image.size

    if min(width, height) < MIN_SIZE:
        return False, "image size too small: {}".format(image.size)

    if max(width, height) > MAX_SIZE:
        return False, "image size too big: {}".format(image.size)

    if isinstance(dpi, float):
        if dpi < MIN_DPI:
            return False, "DPI too small: {}".format(dpi)
    elif isinstance(dpi, tuple):
        dpi_x, dpi_y = dpi
        if dpi_x < MIN_DPI or dpi_y < MIN_DPI:
            return False, "DPI too small: {}".format(dpi)

    if width * height > MAX_PIXELS:
        return False, "resolution too big: {} x {}".format(width, height)

    return True, ""
