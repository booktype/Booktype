# -*- coding: utf-8 -*-
import StringIO

try:
    import Image
except ImportError:
    from PIL import Image

from django.core.files.base import ContentFile
from ooxml.serialize import HeaderContext

from booktype.utils import config


def convert_image(image_type, content):
    img = Image.open(StringIO.StringIO(content.read()))
    out = StringIO.StringIO()

    img.save(out, format='PNG')
    data = out.getvalue()
    out.close()
    return ContentFile(data)


class DocHeaderContext(object, HeaderContext):

    def is_header(self, elem, font_size, node, style=None):
        """
        Used for checking if specific element is a header or not.

        :Returns:
          True or False
        """

        # TODO: Define with the team what is header and what is not.
        # We should have a predefined list of classes or tags that are
        # considered headers

        return super(DocHeaderContext, self).is_header(elem, font_size, node, style)


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


def hook_infobox_table(ctx, document, el, elem):
    """
    To be a valid infobox, the table should only have two rows and
    one column. Besides that the first row should contain a paragraph with
    the style of infoboxcaption, otherwhise it should be taken as normal table

    Here is a table infobox example (attention: it is on html, not docx format)
    <table>
        <tr>
            <p class="infoboxcaption">Title or caption text here</p>
        </tr>
        <tr>
            <p class="infoboxcontent">
                Content of the box, the style/class here is optional
                This might also contain a cite.
            </p>
        </tr>
    </table>
    """

    if len(el.rows) != 2:
        return

    thead, tbody = elem
    try:
        tcaption = thead[0][0]
    except IndexError:
        return

    if 'infobox' not in tcaption.get('class', ''):
        return

    elem.tag = 'div'
    elem.set('class', 'bk-box')

    thead.tag = 'div'
    thead.set('class', 'box-caption')

    tbody.tag = 'div'
    tbody.set('class', 'box-content')


def clean_infobox_content(tree):
    """
    Clean infobox content from unneccesary tags or headers
    removes td orphan tags and tags of first level of children deep

    :Args:
      - tree (:class:`lxml.html`): HTML tree parsed from string
    """

    # let's first get rid of all td orphans tags from table
    for td in tree.xpath('//div[contains(@class, "bk-box")]//td'):
        td.drop_tag()

    # then we should remove all unneccesary tags inside each bk-box
    for box in tree.xpath('//div[contains(@class, "bk-box")]'):

        # only first level of children deep
        for child in box.xpath('//div[contains(@class, "box-caption")]/*'):
            child.drop_tag()

        for child in box.xpath('//div[contains(@class, "box-content")]/*'):
            child.drop_tag()
