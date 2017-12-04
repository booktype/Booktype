# -*- coding: utf-8 -*-
import os
import hashlib
import logging
import math
from PIL import Image, ImageEnhance, ImageFilter

from django.utils.text import get_valid_filename


logger = logging.getLogger("booktype.convert.image_editor")

class BkImageEditor(object):
    """
    Booktype Image Editor

    Available operations:
     - flip horizontally
     - flip vertically
     - rotate left
     - rotate right
     - crop
     - zoom
     - saturation
     - brightness
     - contrast
     - blur
     - opacity

    Uses Python Image Library (PIL).
    """

    USE_CACHE = True
    QUALITY = 100
    DPI = 300
    EXTENSION_MAP = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'gif': 'GIF',
    }

    def __init__(self, input_image_file, input_image_filename, cache_folder=None):
        """
        :Args:
          - self (:class:`BkImageEditor`): BkImageEditor instance.
        """

        self._input_image_file = input_image_file
        self._input_image_filename = get_valid_filename(input_image_filename)
        self._cache_folder = cache_folder

        self._image_width = None
        self._image_height = None
        self._image_translate_x = None
        self._image_translate_y = None
        self._image_flip_x = None
        self._image_flip_y = None
        self._image_rotate_degree = 0
        self._image_contrast = None
        self._image_brightness = None
        self._image_blur = None
        self._image_saturate = None
        self._image_opacity = None

        self._frame_width = None
        self._frame_height = None

    @property
    def output_filename(self):
        ptrn = "{filename}_edited_image" \
               "_iw{image_width}_ih{image_height}" \
               "_tx{image_translate_x}_ty{image_translate_y}" \
               "_fx{image_flip_x}_fy{image_flip_y}" \
               "_rd{image_rotate_degree}" \
               "_con{image_contrast}" \
               "_br{image_brightness}" \
               "_bl{image_blur}" \
               "_sat{image_saturate}" \
               "_op{image_opacity}" \
               "_fw{frame_width}_fh{frame_height}" \
               ".{extension}"

        filename, extension = self._input_image_filename.rsplit('.', 1)

        output_filename = ptrn.format(filename=filename,
                                      image_width=self._image_width, image_height=self._image_height,
                                      image_translate_x=self._image_translate_x,
                                      image_translate_y=self._image_translate_y,
                                      image_flip_x=1 if self._image_flip_x else 0,
                                      image_flip_y=1 if self._image_flip_y else 0,
                                      image_rotate_degree=self._image_rotate_degree,
                                      image_contrast=self._image_contrast,
                                      image_brightness=self._image_brightness,
                                      image_blur=self._image_blur,
                                      image_saturate=self._image_saturate,
                                      image_opacity=self._image_opacity,
                                      frame_width=self._frame_width, frame_height=self._frame_height,
                                      extension=extension.lower())

        return '{cache_hash}.{extension}'.format(
            cache_hash=hashlib.md5(output_filename).hexdigest(),
            extension=extension.lower()
        )

    def process(self, image_width, image_height, image_translate_x,
                image_translate_y, image_flip_x, image_flip_y, image_rotate_degree, image_contrast,
                image_brightness, image_blur, image_saturate, image_opacity, frame_width, frame_height):
        """
        Run process operations under image and return edited image path.
        If USE_CACHE is enabled and cache exists, method returns cached image path.

        :Args:
          - self (:class:`BkImageEditor`): BkImageEditor instance.
          - image_width (:class:`int`): Resize image to selected width.
          - image_height (:class:`int`): Resize image to selected height.
          - image_translate_x (:class:`int`): Move image by X axis. 0:0 is frame left top corner.
          - image_translate_y (:class:`int`): Move image by Y axis. 0:0 is frame left top corner.
          - image_flip_x (:class:`bool`): Flip image X axis.
          - image_flip_y (:class:`bool`): Flip image Y axis.
          - image_rotate_degree (:class:`int`): Rotate image degree.
          - image_contrast (:class:`int`): Image contrast level.
          - image_brightness (:class:`int`): Image brightness level.
          - image_blur (:class:`int`): Image blur level.
          - image_saturate (:class:`int`): Image saturate level.
          - image_opacity (:class:`int`): Image opacity level.
          - frame_width (:class:`int`): Frame/crop area width.
          - frame_height (:class:`int`): Frame/crop area height.

        :Returns:
          Path to edited image
        """

        self._image_width = image_width
        self._image_height = image_height
        self._image_translate_x = image_translate_x
        self._image_translate_y = image_translate_y
        self._image_flip_x = image_flip_x
        self._image_flip_y = image_flip_y
        self._image_rotate_degree = image_rotate_degree
        self._image_contrast = image_contrast
        self._image_brightness = image_brightness
        self._image_blur = image_blur
        self._image_saturate = image_saturate
        self._image_opacity = image_opacity
        self._frame_width = frame_width
        self._frame_height = frame_height

        output_filepath = os.path.join(self._cache_folder, self.output_filename)

        # cache folder
        if not os.path.exists(self._cache_folder):
            # folder can be created by another process between os.path.exists and os.makedirs
            try:
                os.makedirs(self._cache_folder)
            except OSError:
                pass

        if self.USE_CACHE:
            if os.path.exists(output_filepath):
                return output_filepath

        try:

            # converted to have an alpha layer
            pil_region = self._input_image_file.convert(self._input_image_file.mode)

            # try to get icc profile
            try:
                icc_profile = self._input_image_file.info.get("icc_profile")
            except:
                icc_profile = None

            # resize image (not frame)
            pil_region = pil_region.resize(
                (self._image_width, self._image_height),
                Image.ANTIALIAS
            )

            # scale image (flip)
            if self._image_flip_x:
                pil_region = pil_region.transpose(Image.FLIP_LEFT_RIGHT)

            if self._image_flip_y:
                pil_region = pil_region.transpose(Image.FLIP_TOP_BOTTOM)

            # rotate image
            if self._image_rotate_degree != 0:
                pil_region = pil_region.rotate(self._image_rotate_degree)

            # apply frame cropping
            if self._image_rotate_degree in (-270, -90, 90, 270):
                xsize, ysize = self._image_width, self._image_height

                # initial image left-top coordiantes relatively to the frame
                x, y = self._image_translate_x, self._image_translate_y

                # image center coordinates
                xc = x + xsize / 2
                yc = y + ysize / 2

                # rotate degree
                rotate_deg = self._image_rotate_degree
                rotate_radians = math.radians(rotate_deg)

                # calculate left-top image coordinates (relatively to the frame) after rotation
                # used formula:
                # X = x0 + (x - x0) * cos(a) - (y - y0) * sin(a)
                # Y = y0 + (y - y0) * cos(a) + (x - x0) * sin(a)
                x1 = xc + (x - xc) * math.cos(rotate_radians) - (y - yc) * math.sin(rotate_radians)
                y1 = yc + (y - yc) * math.cos(rotate_radians) + (x - xc) * math.sin(rotate_radians)

                if rotate_deg in (-270, 90):
                    x1 -= ysize
                # -90, 270
                else:
                    y1 -= xsize

                frame = (
                    int(x1) * (-1),
                    int(y1) * (-1),
                    int(x1) * (-1) + self._frame_width,
                    int(y1) * (-1) + self._frame_height
                )
            else:
                frame = (
                    self._image_translate_x * (-1),
                    self._image_translate_y * (-1),
                    self._image_translate_x * (-1) + self._frame_width,
                    self._image_translate_y * (-1) + self._frame_height
                )

            pil_region = pil_region.crop(frame)

            # contrast
            contr = ImageEnhance.Contrast(pil_region)
            pil_region = contr.enhance(self._image_contrast)

            # brightness
            brightness = ImageEnhance.Brightness(pil_region)
            pil_region = brightness.enhance(self._image_brightness)

            # saturate
            saturate = ImageEnhance.Color(pil_region)
            pil_region = saturate.enhance(self._image_saturate)

            # blur
            # TODO test this part one more time
            pil_region = pil_region.filter(ImageFilter.GaussianBlur(self._image_blur))

            if icc_profile:
                pil_region.save(output_filepath, quality=self.QUALITY, dpi=(self.DPI, self.DPI),
                                icc_profile=icc_profile)
            else:
                pil_region.save(output_filepath, quality=self.QUALITY, dpi=(self.DPI, self.DPI))

            return output_filepath

        except (IOError, Exception) as e:
            logger.exception("BkImageEditor: {}. Image: {}".format(e.message, self._input_image_file) )
            return None
