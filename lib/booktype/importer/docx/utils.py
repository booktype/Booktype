# -*- coding: utf-8 -*-
import StringIO

try:
    import Image
except ImportError:
    from PIL import Image

from django.core.files.base import ContentFile


def convert_image(image_type, content):
    img = Image.open(StringIO.StringIO(content.read()))
    out = StringIO.StringIO()

    img.save(out, format='PNG')
    data = out.getvalue()
    out.close()
    return ContentFile(data)
