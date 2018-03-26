import os
import json
import shutil
import ebooklib
import StringIO
import logging
import subprocess

from django.conf import settings

from booktype.utils import config
from booktype.utils.image_editor import BkImageEditor

try:
    import Image
except ImportError:
    from PIL import Image


logger = logging.getLogger("booktype.convert")

EDITOR_WIDTH = config.get_configuration('CONVERT_EDITOR_WIDTH')


class ImageEditorConversion(object):

    def __init__(self, original_book, output_document_width, converter):
        self._original_book = original_book
        self._output_document_width = output_document_width
        self._converter = converter

        # cache path for edited images
        # example: /data/tmp/bk_image_editor/<project_id>
        self._cache_folder = os.path.abspath(
            os.path.join(settings.MEDIA_ROOT, 'bk_image_editor', self._converter.config.get("project_id"))
        )

        # we are using this internal image state in _edit_image method
        self._image_state = {
            'layout': None,
            'layout_count_images': 0,
            'image_width_%': 0,
            'caption_width': 0
        }

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

                    if not hasattr(settings, 'COLOR_SPACE_CONVERTER'):
                        warn_msg = [
                            '`COLOR_SPACE_CONVERTER` value is not specified in settings file.',
                            'Color space conversion not running.']
                        logger.warn(" ".join(warn_msg))

                    if getattr(settings, 'COLOR_SPACE_CONVERTER', False):
                        self._color_space_convert(img_element)

        return html

    def _edit_image(self, elem):
        """
        Edit image
        """
        ebooklib_item_image = None
        src = elem.get('src')
        div_image = elem.getparent()
        div_wrap = None
        div_group_img = div_image.getparent()

        if div_group_img.get('class') and 'wrap' in div_group_img.get('class'):
            div_wrap = div_group_img
            div_group_img = div_wrap.getparent()

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

        transform_data = json.loads(elem.get('transform-data'))
        del elem.attrib['transform-data']

        ###########################
        # resize && update styles #
        ###########################

        # proportionally resize according to self._output_document_width
        quotient = float(EDITOR_WIDTH) / float(self._output_document_width)

        transform_data['imageWidth'] = float(transform_data['imageWidth']) / quotient
        transform_data['frameWidth'] = float(transform_data['frameWidth']) / quotient
        transform_data['imageHeight'] = float(transform_data['imageHeight']) / quotient
        transform_data['frameHeight'] = float(transform_data['frameHeight']) / quotient
        transform_data['imageTranslateX'] = float(transform_data['imageTranslateX']) / quotient
        transform_data['imageTranslateY'] = float(transform_data['imageTranslateY']) / quotient

        # full page image
        if transform_data.get('frameFPI'):
            # proportionally resize, fpi width must be equal document width
            quotient = transform_data['frameWidth'] / float(self._output_document_width)

            transform_data['imageWidth'] = float(transform_data['imageWidth']) / quotient
            transform_data['frameWidth'] = float(transform_data['frameWidth']) / quotient
            transform_data['imageHeight'] = float(transform_data['imageHeight']) / quotient
            transform_data['frameHeight'] = float(transform_data['frameHeight']) / quotient
            transform_data['imageTranslateX'] = float(transform_data['imageTranslateX']) / quotient
            transform_data['imageTranslateY'] = float(transform_data['imageTranslateY']) / quotient

            # mark element with fpi class
            elem.set('class', 'fpi')

        # this solution work with kindle
        width_percent = 100 - (100 - 100 * float(transform_data['frameWidth']) / self._output_document_width)
        self._image_state['image_width_%'] = round(width_percent, 1)

        # detect image layout
        if div_group_img.get('class') and 'image-layout-' in div_group_img.get('class'):
            _layout = div_group_img.get('class').rsplit('image-layout-', 1)[-1]

            if _layout == self._image_state['layout']:
                self._image_state['layout'] = _layout
                # it means that we switched to a new layout, for now only 2 images can be in a container
                if self._image_state['layout_count_images'] >= 2:
                    self._image_state['layout_count_images'] = 1
                else:
                    self._image_state['layout_count_images'] += 1
            else:
                # switched to a new layout, it means that current image is 1st in this container
                self._image_state['layout'] = _layout
                self._image_state['layout_count_images'] = 1

        # set img or div.wrap width
        if self._image_state['layout'] in ('2images', '2images_1caption_bottom'):
            elem.set('style', ' width: {0}%;'.format(self._image_state['image_width_%'] - 0.6))
        elif self._image_state['layout'] == '2images_2captions_bottom':
            div_wrap.set('style', ' width: {0}%;'.format(self._image_state['image_width_%'] - 0.6))
        else:
            elem.set('style', ' width: {0}%;'.format(self._image_state['image_width_%']))

        if not transform_data.get('frameFPI'):
            # we don't need this wrapper
            div_image.drop_tag()

            # find old captions using p.caption_small
            for p_caption in div_group_img.xpath('p[contains(@class,"caption_small")]'):
                if p_caption.get('style'):
                    del p_caption.attrib['style']

                if p_caption.get('class'):
                    del p_caption.attrib['class']

                # set new class and change tag
                p_caption.set('class', 'caption_small')
                p_caption.tag = 'div'

            # calculate width for caption for different layouts
            if self._image_state['layout'] in ('1image_1caption_left', '1image_1caption_right'):
                self._image_state['caption_width'] = round(100 - self._image_state['image_width_%'], 1)
            elif self._image_state['layout'] == '2images_1caption_bottom':
                if self._image_state['layout_count_images'] == 1:
                    self._image_state['caption_width'] = self._image_state['image_width_%']
                else:
                    self._image_state['caption_width'] += self._image_state['image_width_%']
            else:
                self._image_state['caption_width'] = self._image_state['image_width_%']

            new_style = 'width: {0}%;'.format(self._image_state['caption_width'])

            # set width for caption div
            if (self._image_state['layout'] != '2images_1caption_bottom' or self._image_state['layout_count_images'] == 2):
                caption_container = div_group_img

                if self._image_state['layout'] == '2images_2captions_bottom':
                    caption_container = div_wrap
                    new_style = 'width: 100%;'

                for div_caption in caption_container.xpath('div[contains(@class,"caption_small")]'):
                    try:
                        text_align = div_group_img.get('style').split('text-align: ', 1)[1].split(';', 1)[0]
                        if text_align == 'center':
                            new_style += ' text-align: center;'
                        elif text_align == 'right':
                            new_style += ' text-align: right;'
                        else:
                            new_style += ' text-align: left;'
                    except (KeyError, Exception):
                        pass

                    if self._image_state['layout'] in ('1image_1caption_bottom', '2images_1caption_bottom'):
                        # text-align: left -> margin-right: auto
                        # text-align: right -> margin-left: auto
                        # text-align: center -> margin: auto
                        # text-align: justify -> margin-right: auto
                        try:
                            text_align = div_group_img.get('style').split('text-align: ', 1)[1].split(';', 1)[0]
                            if text_align == 'center':
                                new_style += ' margin-left: auto; margin-right: auto;'
                            elif text_align == 'right':
                                new_style += ' margin-left: auto;'
                            else:
                                new_style += ' margin-right: auto;'
                        except (KeyError, Exception):
                            pass

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

        # copy edited image into export package,
        # to have everything we need in one place
        dst = os.path.join(
            os.path.dirname(self._converter.images_path),
            os.path.basename(output_image_path)
        )

        if not os.path.exists(self._converter.images_path):
            os.makedirs(self._converter.images_path)

        shutil.copy(output_image_path, self._converter.images_path)

        # change image src in html
        elem.set("src", dst)

    def _color_space_convert(self, elem, rgb_icc_profile_path=None, cmyk_icc_profile_path=None):

        if rgb_icc_profile_path is None or cmyk_icc_profile_path is None:
            try:
                rgb_icc_profile_path = settings.CMYK2RGB_CONVERTER_RGB_PROFILE_PATH
                cmyk_icc_profile_path = settings.CMYK2RGB_CONVERTER_CMYK_PROFILE_PATH
            except AttributeError as err:
                logger.warning("Color space conversion not running. Details: %s" % err)
                return

            if not hasattr(self._converter, 'images_color_model'):
                logger.warning('Converter "{}" has not "images_color_model" attribute.'.format(
                    self._converter
                ))
                return

            if self._converter.images_color_model not in ('RGB', 'CMYK'):
                logger.warning('Unsupported "images_color_model" attribute value: "{}", in converter: {}'.format(
                    self._converter.images_color_model,
                    self._converter
                ))
                return

        src = elem.get('src')
        image_mode = None
        cmd = None

        # get image mode
        # http://pillow.readthedocs.io/en/3.4.x/handbook/concepts.html#modes
        with Image.open(src) as image:
            image_mode = image.mode

            # validate color space
            if image_mode not in ('CMYK', 'RGB'):
                logger.warning('Unsupported color space "{}" in image: {}. It will be converted to RGB'.format(
                    image_mode,
                    src
                ))

                # convert RGBA to RGB
                if image_mode == 'RGBA':
                    png = image
                    # required for png.split()
                    png.load()
                    jpeg = Image.new("RGB", png.size, (255, 255, 255))
                    jpeg.paste(png, mask=png.split()[3])
                    src = '{}.jpeg'.format(src.rsplit('.', 1)[0])
                    jpeg.save(src, 'JPEG', quality=100)
                    image_mode = "RGB"
                    # remove old image
                    os.remove(elem.get('src'))
                    # set new image for an element
                    elem.set('src', src)

        # convert CMYK to RGB
        if self._converter.images_color_model == 'RGB' and image_mode == 'CMYK':
            cmd = '{0} -profile "{1}" {2} -profile "{3}" {4}'.format(
                settings.IMAGEMAGICK_PATH,
                cmyk_icc_profile_path,
                src,
                rgb_icc_profile_path,
                src
            )
        # convert RGB to CMYK
        elif self._converter.images_color_model == 'CMYK' and image_mode == 'RGB':
            cmd = '{0} -profile "{1}" {2} -profile "{3}" {4}'.format(
                settings.IMAGEMAGICK_PATH,
                rgb_icc_profile_path,
                src,
                cmyk_icc_profile_path,
                src
            )
        else:
            return

        if cmd:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()

            if err:
                logger.error('Error during converting color spaces. Error {0}. CMD: {1}'.format(err, cmd))
            else:
                logger.info('Converting color spaces command "{}" executed with output: "{}"'.format(cmd, out))
