# -*- coding: utf-8 -*-
import uuid
import StringIO

try:
    import Image
except ImportError:
    from PIL import Image

from django.core.files.base import ContentFile
from ooxml.serialize import HeaderContext

from booktype.utils import config
from booktype.utils.misc import import_from_string


def convert_image(image_type, content):
    img = Image.open(StringIO.StringIO(content.read()))
    out = StringIO.StringIO()

    img.save(out, format='PNG')
    data = out.getvalue()
    out.close()
    return ContentFile(data)


def get_importer_class():
    """
    Dummy function to return the correct module to import DOCX files.
    If there is no custom class specified in client instance, it will use
    .docximporter.WordImporter class as it is in constants.py file
    """

    DOCX_IMPORTER_CLASS = config.get_configuration('DOCX_IMPORTER_CLASS')
    ImporterClass = import_from_string(DOCX_IMPORTER_CLASS)
    return ImporterClass


class DocHeaderContext(object, HeaderContext):

    def is_header(self, elem, font_size, node, style=None):
        """
        Used for checking if specific element is a header or not.

        :Returns:
          True or False
        """

        HEADING_STYLES = config.get_configuration('DOCX_HEADING_STYLES', [])

        # Check the defined list of styles
        if style:
            if style.style_id.lower() in HEADING_STYLES:
                return True

        if elem.rpr.get('style', None):
            for style_key in HEADING_STYLES:
                if elem.rpr.get('style').lower().replace('-', '').startswith(style_key):
                    return True

        for e in elem.elements:
            if hasattr(e, 'rpr'):
                if e.rpr.get('style', None):
                    for style_key in HEADING_STYLES:

                        if e.rpr.get('style').lower().replace('-', '').startswith(style_key):
                            return True

        return super(DocHeaderContext, self).is_header(elem, font_size, node, style)

    def get_header(self, elem, style, node):
        """
        Returns HTML tag representing specific header for this element.

        :Returns:
          String representation of HTML tag.
        """

        STYLES_TUPLE = config.get_configuration('DOCX_HEADING_STYLES_TUPLE')

        if style and not isinstance(style, int):
            for header_id, header_values in STYLES_TUPLE:
                if style.style_id.lower().replace('-', '') in header_values:
                    return header_id

        if elem.rpr.get('style', None):
            for header_id, header_values in STYLES_TUPLE:
                for style_key in header_values:
                    if elem.rpr.get('style').lower().replace('-', '').startswith(style_key):
                        return header_id

        for e in elem.elements:
            if hasattr(e, 'rpr'):
                if e.rpr.get('style', None):
                    for header_id, header_values in STYLES_TUPLE:
                        for style_key in header_values:
                            if e.rpr.get('style').lower().replace('-', '').startswith(style_key):
                                return header_id

        return super(DocHeaderContext, self).get_header(elem, style, node)


def serialize_empty(ctx, document, elem, root):
    return root


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


def hook_footnote(ctx, document, el, elem):
    """
    Hook for the footnotes elements.
    We do not support footnotes by default. We will add a warning
    asking to convert to endnotes and import again
    """

    return


def hook_endnote(ctx, document, el, elem):
    """
    Hook for the endnotes elements.
    Add custom endnote booktype class and remove link tag.
    """

    data_id = str(uuid.uuid1()).replace('-', '')

    elem.set('class', 'endnote')
    elem.set('data-id', data_id)

    # this will be used later to retrieve content of endnote
    elem.set('data-relationship', 'endnotes')
    elem.set('data-relation-id', el.rid)


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


def fix_citations(tree):
    """
    Sometimes citations are inline elements so the hook for paragraph
    is not able to match the styles to set the right class and tag. This
    is just for citations for now. We should improve this logic later

    :Args:
      - tree (:class:`lxml.html`): HTML tree parsed from string
    """

    for cite in tree.xpath('//*[contains(@class, "citation")]'):
        cite.tag = 'p'
        cite.set('class', 'bk-cite')
