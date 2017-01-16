# -*- coding: utf-8 -*-
import os
import ebooklib
import StringIO
import logging

from lxml import etree
from ebooklib.plugins.base import BasePlugin

from django.conf import settings

from booktype.utils.image_editor import BkImageEditor

from .constants import IMAGES_DIR


try:
    import Image
except ImportError:
    from PIL import Image

logger = logging.getLogger("booktype.convert.epub")


class ImageEditorWriterPlugin(BasePlugin):
    """
    Plugin for image editing
    """

    def __init__(self, cache_subdirectory, *args, **kwargs):
        super(ImageEditorWriterPlugin, self).__init__(*args, **kwargs)

        self._cache_subdirectory = cache_subdirectory
        # cache path for edited images
        # example: /data/tmp/bk_image_editor/<project_id>
        self.cache_folder = os.path.abspath(
            os.path.join(settings.MEDIA_ROOT, 'bk_image_editor', self._cache_subdirectory)
        )
        self._ebooklib_item_image_id = 0
        self._is_initial_epub_images_removed = False

    def html_before_write(self, book, item):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            return True

        if isinstance(item, ebooklib.epub.EpubNav):
            return True

        self._remove_initial_epub_images(book)

        root = ebooklib.utils.parse_html_string(item.content)

        for img_element in root.iter('img'):
            if img_element.get('src'):
                # validate image extension
                extension = img_element.get('src').rsplit('.', 1)[1].lower()

                if extension in BkImageEditor.EXTENSION_MAP:
                    self._write_edited_image(book, img_element)

        item.content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True

    def _write_edited_image(self, book, elem):
        src = elem.get('src')
        src_filename = src.rsplit('/')[-1]

        # find existing ebook image object
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if item.file_name.rsplit('/')[-1] == src_filename:
                break
        # create ebooklib image item
        else:
            edited_image_path = os.path.join(self.cache_folder, src_filename)

            if os.path.isfile(edited_image_path):

                # buffer for future epub image object
                output_io = StringIO.StringIO()

                # save edited image to the buffer
                with Image.open(edited_image_path) as im:
                    extension = edited_image_path.rsplit('.', 1)[1].lower()
                    im.save(
                        output_io,
                        BkImageEditor.EXTENSION_MAP.get(extension, 'JPEG'),
                        quality=BkImageEditor.QUALITY,
                        dpi=(BkImageEditor.DPI, BkImageEditor.DPI)
                    )

                    # create new epub.EpubImage
                    new_ebooklib_item_image = ebooklib.epub.EpubImage()
                    new_ebooklib_item_image.id = 'edited_image_{0}'.format(self._ebooklib_item_image_id)
                    new_ebooklib_item_image.set_content(output_io.getvalue())

                    # close buffer for output image file
                    output_io.close()

                    # change image src in html
                    elem.set("src", src)
                    # set filename for epub object
                    new_ebooklib_item_image.file_name = u'{}/{}'.format(IMAGES_DIR, src_filename)
                    # add epub.EpubImage to the book
                    book.add_item(new_ebooklib_item_image)

                    # counter++
                    self._ebooklib_item_image_id += 1

    def _remove_initial_epub_images(self, book):
        if self._is_initial_epub_images_removed:
            return

        for item in [image_item for image_item in book.get_items_of_type(ebooklib.ITEM_IMAGE)]:
            book.items.remove(item)

        self._is_initial_epub_images_removed = True
