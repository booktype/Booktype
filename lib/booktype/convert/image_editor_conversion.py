import os
import json
import ebooklib
import StringIO
import logging

from django.conf import settings

from booktype.utils.image_editor import BkImageEditor

try:
    import Image
except ImportError:
    from PIL import Image

EDITOR_WIDTH = 898


logger = logging.getLogger("booktype.convert.pdf")


class ImageEditorConversion(object):

    def __init__(self, original_book, output_document_width, project_id):
        self._original_book = original_book
        self._output_document_width = output_document_width

        # cache path for edited images
        # example: /data/tmp/bk_image_editor/<project_id>
        self._cache_folder = os.path.abspath(
            os.path.join(settings.MEDIA_ROOT, 'bk_image_editor', project_id)
        )

    def convert(self, html):
        """
        Parse html, search for image and edit it
        """
        for img_element in html.iter('img'):
            if img_element.get('src'):
                # validate image extension
                extension = img_element.get('src').rsplit('.', 1)[1].lower()

                if extension in BkImageEditor.EXTENSION_MAP:
                    self._edit_image(img_element)

        return html

    def _edit_image(self, elem):
        """
        Edit image
        """
        ebooklib_item_image = None
        src = elem.get('src')
        div_image = elem.getparent()
        div_group_img = div_image.getparent()

        ##############################
        # image structure inside <a> #
        ##############################
        if div_group_img.getparent() is not None and div_group_img.getparent().tag == 'a':
            div_group_img.drop_tag()
            div_image.drop_tag()

            if elem.get('transform-data'):
                del elem.attrib['transform-data']

            if elem.get('style'):
                del elem.attrib['style']

            if elem.get('width'):
                del elem.attrib['width']

            if elem.get('height'):
                del elem.attrib['height']

            elem.set('style', 'display: inline-block;')

            return

        ###########################
        # find ebook image object #
        ###########################
        for item in self._original_book.get_items_of_type(ebooklib.ITEM_IMAGE):

            if item.file_name.rsplit('/')[-1] == src.rsplit('/')[-1]:
                ebooklib_item_image = item
                break
        # we didn't find image object
        else:
            if elem.get('transform-data'):
                del elem.attrib['transform-data']

            return

        ###########################
        # validate transform-data #
        ###########################
        try:
            transform_data = json.loads(elem.get('transform-data'))

            if transform_data['imageWidth'] < 50:
                transform_data['imageWidth'] = 50

            if transform_data['imageHeight'] < 50:
                transform_data['imageHeight'] = 50

            if transform_data['frameWidth'] < 50:
                transform_data['frameWidth'] = 50

            if transform_data['frameHeight'] < 50:
                transform_data['frameHeight'] = 50

            elem.set('transform-data', json.dumps(transform_data))

        except (ValueError, Exception) as e:
            if elem.get('transform-data'):
                del elem.attrib['transform-data']

        #################################
        # create default transform-data #
        #################################
        if not elem.get('transform-data'):

            transform_data = {
                'imageWidth': None,
                'imageHeight': None,
                'imageTranslateX': 0,
                'imageTranslateY': 0,
                'imageScaleX': 1,
                'imageScaleY': 1,
                'imageRotateDegree': 0,
                'imageContrast': 100,
                'imageBrightness': 100,
                'imageBlur': 0,
                'imageSaturate': 100,
                'imageOpacity': 100,
                'frameWidth': None,
                'frameHeight': None,
                'editorWidth': EDITOR_WIDTH
            }

            div_image_style = div_image.get('style', '')

            if 'width: ' in div_image_style and 'height: ' in div_image_style:
                width = div_image_style.rsplit('width: ')[1].split('px', 1)[0]
                height = div_image_style.rsplit('height: ')[1].split('px', 1)[0]
                transform_data['imageWidth'] = transform_data['frameWidth'] = width
                transform_data['imageHeight'] = transform_data['frameHeight'] = height
            else:
                # get natural image width and height
                with Image.open(StringIO.StringIO(item.get_content())) as im:
                    natural_width, natural_height = im.size

                    if natural_width <= EDITOR_WIDTH:
                        transform_data['imageWidth'] = transform_data['frameWidth'] = natural_width
                        transform_data['imageHeight'] = transform_data['frameHeight'] = natural_height
                    else:
                        # this should be done with quotient
                        quotient = EDITOR_WIDTH / float(natural_width)
                        transform_data['imageWidth'] = transform_data['frameWidth'] = float(natural_width) * quotient
                        transform_data['imageHeight'] = transform_data['frameHeight'] = float(natural_height) * quotient

            # record transform_data
            elem.set('transform-data', json.dumps(transform_data))

        ##########################
        # delete redundant attrs #
        ##########################
        if elem.get('style'):
            del elem.attrib['style']

        if elem.get('width'):
            del elem.attrib['width']

        if elem.get('height'):
            del elem.attrib['height']

        if div_image.get('style'):
            del div_image.attrib['style']

        ###########################
        # resize && update styles #
        ###########################
        transform_data = json.loads(elem.get('transform-data'))
        del elem.attrib['transform-data']

        # proportionally resize according to self._output_document_width
        quotient = float(EDITOR_WIDTH) / float(self._output_document_width)

        transform_data['imageWidth'] = float(transform_data['imageWidth']) / quotient
        transform_data['frameWidth'] = float(transform_data['frameWidth']) / quotient
        transform_data['imageHeight'] = float(transform_data['imageHeight']) / quotient
        transform_data['frameHeight'] = float(transform_data['frameHeight']) / quotient
        transform_data['imageTranslateX'] = float(transform_data['imageTranslateX']) / quotient
        transform_data['imageTranslateY'] = float(transform_data['imageTranslateY']) / quotient

        # TODO handle full page images
        # set style for image
        image_style = 'display: inline-block;'

        # this solution work with kindle
        width_percent = 100 - (100 - 100 * float(transform_data['frameWidth']) / self._output_document_width)
        width_percent = round(width_percent, 1)
        image_style += ' width: {0}%;'.format(width_percent)

        # TODO only for epub
        elem.set('style', image_style)

        # set width for caption div
        for div_caption in div_group_img.xpath('div[contains(@class,"caption_small")]'):

            try:
                width = div_caption.get('style').rsplit('width: ')[1].split('px', 1)[0]
                old_style = div_caption.get('style')
                new_style = old_style.replace('width: {}px'.format(width), 'width: {}%'.format(width_percent))
            except:
                new_style = div_caption.get('style', '') + 'width: {}%;'.format(width_percent)
                logger.warning('Wrong image caption style structure')

            div_caption.set('style', new_style)

        #################
        # start editing #
        #################

        # cache path for edited images
        # example: /data/tmp/bk_image_editor/<project_id>
        cache_folder = os.path.abspath(
            os.path.join(settings.MEDIA_ROOT, 'bk_image_editor', self._cache_folder)
        )

        output_image_path = None
        input_image_filename = ebooklib_item_image.file_name.rsplit('/')[-1]

        with Image.open(StringIO.StringIO(ebooklib_item_image.get_content())) as img:

            ie = BkImageEditor(input_image_file=img, input_image_filename=input_image_filename,
                               cache_folder=cache_folder)

            output_image_path = ie.process(
                image_width=int(transform_data['imageWidth']),
                image_height=int(transform_data['imageHeight']),
                image_translate_x=int(transform_data['imageTranslateX']),
                image_translate_y=int(transform_data['imageTranslateY']),
                image_flip_x=bool(-1 == int(transform_data['imageScaleX'])),
                image_flip_y=bool(-1 == int(transform_data['imageScaleY'])),
                image_rotate_degree=int(transform_data['imageRotateDegree']) * (-1),
                image_contrast=float(transform_data['imageContrast']) / 100,
                image_brightness=float(transform_data['imageBrightness']) / 100,
                image_blur=float(transform_data['imageBlur']),
                image_saturate=float(transform_data['imageSaturate']) / 100,
                image_opacity=int(transform_data['imageOpacity']),
                frame_width=int(transform_data['frameWidth']),
                frame_height=int(transform_data['frameHeight'])
            )

        # semething went wrong
        if not output_image_path or not os.path.isfile(output_image_path):
            return

        # change image src in html
        elem.set("src", output_image_path)
