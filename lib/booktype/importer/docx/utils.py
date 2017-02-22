# -*- coding: utf-8 -*-
import StringIO

try:
    import Image
except ImportError:
    from PIL import Image

from django.core.files.base import ContentFile
from booktype.utils import config


def convert_image(image_type, content):
    img = Image.open(StringIO.StringIO(content.read()))
    out = StringIO.StringIO()

    img.save(out, format='PNG')
    data = out.getvalue()
    out.close()
    return ContentFile(data)


def hook_p(ctx, document, el, elem):
    """
    Hook for the paragraph elements.
    Add different classes used in the editor for different paragraph elements.
    """

    P_STYLES = config.get_configuration('DOCX_PARAGRAPH_STYLES_MAP', {})

    if hasattr(el, 'style_id'):
        class_name = P_STYLES.get(el.style_id, None)

        if class_name:
            elem.set('class', class_name)


def check_h_tags_hook(ctx, document, el, elem):
    """
    This hook just checks if the are H tags with some wrong classes like
    H tags with paragraps classes which is wrong.
    """

    P_STYLES = config.get_configuration('DOCX_PARAGRAPH_STYLES_MAP', {})

    if hasattr(el, 'style_id'):
        class_name = P_STYLES.get(el.style_id, None)

        # if h tag was found with paragraps class, let's switch tag
        if class_name:
            elem.tag = 'p'
            elem.set('class', class_name)
