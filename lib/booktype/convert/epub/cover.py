# -*- coding: utf-8 -*-
from ebooklib import epub

from .constants import (
    DOCUMENTS_DIR,
    IMAGES_DIR
)


COVER_XML = """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>%(book_title)s</title>
    </head>
    <body id="template" xml:lang="%(language)s" style="margin:0px; text-align: center; vertical-align: middle; background-color:#fff;">
        <div>
            <img src="%(cover_path)s" style="height:100%%; text-align:center"/>
        </div>
    </body>
</html>
"""

COVER_UID = 'cover'
COVER_TITLE = 'Cover'
COVER_FILE_NAME = 'cover.xhtml'

IMAGE_UID = 'cover_image'
IMAGE_FILE_NAME = 'cover.jpg'


def add_cover(epub_book, cover_asset, language='en', cover_title=COVER_TITLE):
    """
    Adds cover image to the given book
    """

    cover_path = '../{}/{}'.format(IMAGES_DIR, IMAGE_FILE_NAME)
    cover_data = {
        'book_title': epub_book.title,
        'language': language,
        'cover_path': cover_path
    }
    item = epub.EpubHtml(
        uid=COVER_UID,
        title=cover_title,
        file_name='{}/{}'.format(DOCUMENTS_DIR, COVER_FILE_NAME),
        content=COVER_XML % cover_data
    )

    epub_book.add_item(item)
    epub_book.spine.insert(0, item)

    epub_book.guide.insert(0, {
        'type': 'cover',
        'href': '{}/{}'.format(DOCUMENTS_DIR, COVER_FILE_NAME),
        'title': item.title,
    })

    image_file = open(cover_asset.file_path, 'rb')

    image = epub.EpubCover()
    image.id = IMAGE_UID
    image.file_name = '{}/{}'.format(IMAGES_DIR, IMAGE_FILE_NAME)
    image.set_content(image_file.read())

    epub_book.add_item(image)

    image_file.close()

    epub_book.add_metadata(
        None, 'meta', '', {
            'name': 'cover',
            'content': IMAGE_UID
        }
    )
