# -*- coding: utf-8 -*-
import os
import ebooklib
import StringIO
import logging

from lxml import etree
from ebooklib.plugins.base import BasePlugin

from django.conf import settings

from booktype.apps.themes.utils import read_theme_assets
from booktype.utils.image_editor import BkImageEditor
from ..constants import IMAGES_DIR
from ..cover import IMAGE_FILE_NAME

try:
    import Image
except ImportError:
    from PIL import Image

logger = logging.getLogger("booktype.convert.epub")


class ImageEditorWriterPlugin(BasePlugin):
    """
    Plugin for image editing
    """

    def __init__(self, converter, *args, **kwargs):
        super(ImageEditorWriterPlugin, self).__init__(*args, **kwargs)

        self._converter = converter
        self._cache_subdirectory = self._converter.config.get("project_id")
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

                    # full page image
                    img_element_class = img_element.get('class')
                    if img_element_class and 'fpi' in img_element_class:
                        self._apply_full_page(img_element)

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

    def _get_theme_images(self):
        theme_assets = read_theme_assets(self._converter.theme_name, self._converter.name)
        return [os.path.basename(x) for x in theme_assets.get('images', [])]

    def _remove_initial_epub_images(self, book):
        if self._is_initial_epub_images_removed:
            return

        WHITELIST = self._get_theme_images() + [IMAGE_FILE_NAME]

        for item in [x for x in book.get_items_of_type(ebooklib.ITEM_IMAGE)]:
            image_name = os.path.basename(item.file_name)

            if image_name not in WHITELIST:
                book.items.remove(item)

        self._is_initial_epub_images_removed = True

    def _apply_full_page(self, elem):
        div_image = elem.getparent()
        div_group_img = div_image.getparent()

        # remove cpation
        caption = div_group_img.xpath('.//div[@class="caption_small"]')
        if caption:
            div_group_img.remove(caption[0])

        # remove wrapper
        div_group_img.drop_tag()

        # make it fpi
        elem.set('style', 'width: 100%;')
