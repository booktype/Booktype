# -*- coding: utf-8 -*-
import os
import ebooklib
import StringIO
import logging

from lxml import etree
from ebooklib.plugins.base import BasePlugin

from django.conf import settings

from booktype.utils.image_editor import BkImageEditor


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
        self._initial_ebooklib_images = {}

    def html_before_write(self, book, item):
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            return True

        if isinstance(item, ebooklib.epub.EpubNav):
            return True

        root = ebooklib.utils.parse_html_string(item.content)

        for img_element in root.iter('img'):
            if img_element.get('src'):
                # validate image extension
                extension = img_element.get('src').rsplit('.', 1)[1].lower()

                if extension in BkImageEditor.EXTENSION_MAP:
                    self._write_edited_image(book, img_element)

        self._remove_extra_images(book, root)

        item.content = etree.tostring(root, pretty_print=True, encoding="utf-8", xml_declaration=True)

        return True

    def _write_edited_image(self, book, elem):

        src = elem.get('src')
        src_filename = src.rsplit('/')[-1]

        ###########################
        # find ebook image object #
        ###########################
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if item.file_name.rsplit('/')[-1] == src_filename:
                ebooklib_item_image = item
                self._initial_ebooklib_images[src] = item
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

                    # create unique name
                    _name = src.rsplit('/', 1)
                    _fname = _name[1].rsplit('.', 1)[0]
                    _fname = _fname.split('_edited_image', 1)[0]

                    _name[1] = _fname + '_edited_image_' + str(self._ebooklib_item_image_id) + '.' + extension
                    new_ebooklib_item_image.file_name = u'/'.join(_name)

                    # add epub.EpubImage to the book
                    book.add_item(new_ebooklib_item_image)

                    # change image src in html
                    elem.set("src", '../' + new_ebooklib_item_image.file_name)

                    # counter++
                    self._ebooklib_item_image_id += 1

    def _remove_extra_images(self, book, root):
        all_images_src = set()

        for element in root.iter("img"):
            all_images_src.add(element.get('src'))

        for initial_src in self._initial_ebooklib_images:
            if initial_src not in all_images_src:
                book.items.remove(self._initial_ebooklib_images[initial_src])

        # reset for the next chapter
        self._initial_ebooklib_images = {}