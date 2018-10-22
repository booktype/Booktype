# This file is part of Booktype.
# Copyright (c) 2013 Borko Jandras <borko.jandras@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import uuid
import codecs
import urllib2
import logging
import datetime
from lxml import etree
import ebooklib
import ebooklib.epub
import ebooklib.utils
from copy import deepcopy

from django.conf import settings
from django.template.loader import render_to_string
from django import template
from django.utils.translation import ugettext_lazy as _

from booktype.apps.convert import plugin
from booktype.apps.themes.utils import (
    read_theme_style, get_single_frontmatter, get_single_endmatter, get_body,
    read_theme_assets, read_theme_asset_content, read_theme_info)
from booktype.apps.convert.templatetags.convert_tags import (
    get_refines, get_metadata)
from booktype.utils.misc import booktype_slugify
from booktype.apps.convert.plugin import SectionsSettingsPlugin
from booktype.convert.image_editor_conversion import ImageEditorConversion

from .toc import TocItem
from ..base import BaseConverter
from ..utils.epub import parse_toc_nav, get_sections_settings
from .. import utils
from .styles import create_default_style, get_page_size, CROP_MARGIN

logger = logging.getLogger("booktype.convert.pdf")


class MPDFConverter(BaseConverter):
    """

    This code creates all required files and then passed them to booktype2mpdf.php script to produce
    final PDF output.

    These are the files we pass to the PHP script:
    - body.html
    - frontmatter.html
    - endmatter.html
    - style.css
    - config.json

    config.json file keeps all required input information like page settings, styling, metadata and etc.
    This file is really just the way how we pass the information to PHP script.

    style.css is produced from Django template we defined. It holds all default, theme and custom styling for
    this specific book.

    frontmatter.html, body.html and endmatter.html are produced from Django template files we defined.

    Customisation can be done in two different ways:

    **Templates**

    List of template files:
    - themes/frontmatter_mpdf.html
    - themes/endmatter_mpdf.html
    - themes/body_mpdf.html
    - themes/style_mpdf.css

    **Extending code**

    You need to create your own convert module and extend this class. After that
    you have a set of methods which you could extend to take full control over your
    PDF production:

    - pre_convert
    - post_convert
    - get_extra_data
    - get_extra_style
    - get_extra_configuration
    - get_extra_body_data
    - get_metadata
    """

    name = 'mpdf'
    verbose_name = _("Printers' PDF")
    support_section_settings = True
    images_color_model = "CMYK"

    _images_dir = "images/"
    _body_pdf_name = "body.pdf"
    _body_html_name = "body.html"

    def __init__(self, *args, **kwargs):
        super(MPDFConverter, self).__init__(*args, **kwargs)

        # absolute path to directory where images are saved
        self.images_path = os.path.join(self.sandbox_path, self._images_dir)
        # image item name -> file name mappings
        self.images = {}
        self.theme_name = ''
        self.theme_plugin = None
        self._bk_image_editor_conversion = None
        self._full_page_images_css = 'div.fpi-page-end { page: normalpage; }\n'

    def pre_convert(self, epub_book):
        """Called before entire process of conversion is called.

        :Args:
          - book: EPUB book object
        """

        # we parse the toc nav before pre_convert to get original content
        # take into account that if you call this after calling super pre_convert
        # you will have unexpected results regarding the section settings logic
        self.original_toc_nav = parse_toc_nav(epub_book)

        # now we call parent pre_convert to run section settings plugin
        super(MPDFConverter, self).pre_convert(epub_book)

        # Not that much needed at the moment
        self.config['page_width'], self.config['page_height'] = get_page_size(self.config['settings'])

        # if crop marks is enabled
        if 'crop_marks' in self.config['settings'] and self.config['settings']['crop_marks'] == 'on':
            crop_margin = CROP_MARGIN

            if 'crop_margin' in self.config['settings']:
                crop_margin = int(self.config['settings']['crop_margin'])

            self.config['page_width_bleed'] = self.config['page_width'] + crop_margin
            self.config['page_height_bleed'] = self.config['page_height'] + crop_margin
        else:
            self.config['page_width_bleed'] = self.config['page_width']
            self.config['page_height_bleed'] = self.config['page_height']

        if self.theme_plugin:
            try:
                self.theme_plugin.pre_convert(epub_book)
            except NotImplementedError:
                pass

        # create image editor conversion instance
        # todo move it to more proper place in the future, and create plugin for it

        # calculate pdf document width
        mm = float(self.config['page_width_bleed'])
        mm -= float(self.config['settings'].get('side_margin', 0)) + float(
            self.config['settings'].get('gutter', 0))
        inches = mm / 10 / 2.54

        self._bk_image_editor_conversion = ImageEditorConversion(
            epub_book, inches * 300, self
        )

    def post_convert(self, book, output_path):
        """Called after entire process of conversion is done.

        :Args:
          - book: EPUB Book object
          - output_path: file path to output file
        """

        if self.theme_plugin:
            try:
                self.theme_plugin.post_convert(book, output_path)
            except NotImplementedError:
                pass

    def _get_dir(self, epub_book):
        m = epub_book.metadata[ebooklib.epub.NAMESPACES["OPF"]]

        def _check(x):
            return x[1] and x[1].get('property', '') == 'bkterms:dir'

        values = filter(_check, m[None])
        if len(values) > 0 and len(values[0]) > 0:
            return values[0][0].lower()

        return 'ltr'

    def get_extra_data(self, book):
        """Returns extra data which will be passed to the front matter and end matter templates.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary.
        """
        return {}

    def get_extra_body_data(self, book):
        """Returns extra data which will be passed to the body templates.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary.
        """

        return {}

    def get_extra_style(self, book):
        """Returns extra data which will be passed to the template rendering styling files.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary.
        """

        return {}

    def get_extra_configuration(self):
        """Returns extra data which will be passed to the configuration file.

        Configuration file is read by booktype2mpdf.php script which calls mPDF library.
        The idea is that we can extend this method and pass some additional information
        to the PHP script.

        :Returns:
          Returns dictionary.
        """

        data = {'mirror_margins': True}

        if self.theme_plugin:
            data['mpdf'] = self.theme_plugin.get_mpdf_config()

        # get additional mpdf configuration options
        data.setdefault('mpdf', {}).update(self._get_theme_mpdf_config())

        return data

    def get_metadata(self, book):
        """Returns metadata which will be passed to the PHP script.

        The idea is that we return certain metadata information which will be written
        to the configuration file. The idea is that booktype2mpdf.php script could
        also get some of the metadata information.

        :Args:
          - book: EPUB Book object

        :Returns:
          Returns dictionary with metadata information.
        """

        dc_metadata = {
            key: value[0][0] for key, value in
            book.metadata.get("http://purl.org/dc/elements/1.1/").iteritems()
        }

        m = book.metadata[ebooklib.epub.NAMESPACES["OPF"]]

        def _check(x):
            if x[1].get('property', '').startswith('add_meta_terms:'):
                return True
            return False

        for key, value in filter(_check, m[None]):
            dc_metadata[value.get('property')] = key

        dc_metadata['bkterms:dir'] = self.direction

        return dc_metadata

    def _init_theme_plugin(self):
        """
        Checks for custom theme's plugin. If no custom plugin if found,
        it will load the mpdf default one
        """

        default_theme_plugin = plugin.MPDFPlugin

        if 'theme' in self.config:
            self.theme_name = self.config['theme'].get('id', '')
            tp = plugin.load_theme_plugin(self.name, self.theme_name)

            self.theme_plugin = tp(self) if tp else default_theme_plugin(self)

    def convert(self, book, output_path):
        """Starts conversion process.

        :Args:
          - book: EPUB Book object
          - output_path: directory path where output files will be saved

        :Returns:
          Returns dictionary with number of pages and file size of output file
        """

        convert_start = datetime.datetime.now()

        self._init_theme_plugin()

        self.direction = self._get_dir(book)

        self.pre_convert(book)

        self._save_images(book)

        self._create_body(book)
        self._write_configuration(book)
        self._create_frontmatter(book)
        self._create_endmatter(book)

        if self.theme_name != '':
            self._add_theme_assets(book)

        self._write_style(book)

        html_path = os.path.join(self.sandbox_path, self._body_html_name)
        pdf_path = os.path.join(self.sandbox_path, self._body_pdf_name)
        data_out = self._run_renderer(html_path, pdf_path)

        os.rename(pdf_path, output_path)

        self.post_convert(book, output_path)

        convert_end = datetime.datetime.now()

        logger.info('Conversion lasted %s.', convert_end - convert_start)

        return {
            "pages": data_out.get('pages', 0),
            "size": os.path.getsize(output_path)
        }

    def _get_chapter_content(self, chapter_item):
        """Returns content of the chapter after some postprocessing.

        This function will also fix certain things in the content. Clear up the links
        pointing to images, remove links for PDF output and etc.

        :Returns:
          Returns strings with HTML content of the chapter.
        """

        base_path = os.path.dirname(chapter_item.file_name)

        try:
            chapter = ebooklib.utils.parse_html_string(chapter_item.content)
            chapter_child = chapter.find("body")

            if chapter_child is not None:
                cnt = deepcopy(chapter_child)
                self._fix_images(cnt, base_path)
                cnt = self._fix_content(cnt)

                if self.theme_plugin:
                    try:
                        cnt = self.theme_plugin.fix_content(cnt)
                    except NotImplementedError:
                        pass

                # todo move it to more proper place in the future, and create plugin for it
                if self._bk_image_editor_conversion:
                    try:
                        cnt = self._bk_image_editor_conversion.convert(cnt)
                    except:
                        logger.exception("mpdf ImageEditorConversion failed")

                self._fix_full_page_image(cnt)

                return etree.tostring(cnt, method='html', encoding='utf-8', pretty_print=True)[6:-9]
        except etree.XMLSyntaxError:
            pass

        return u''

    def _fix_horrible_mpdf(self, content):
        content = content.replace('></columnbreak>', " />\n")
        content = content.replace('></columns>', " />\n")

        return content

    def _create_body(self, book):
        """Create body html file with main content of the book.

        Created html file will be used by booktype2mpdf.php script
        to create final PDF file.

        :Args:
          - book: EPUB Book object
        """

        settings_dict = get_sections_settings(book)

        def _toc(depth, toc_items, parent=None, toc_setting=None):
            items = []
            sec_count = 1

            for toc_item in toc_items:
                # SECTIONS
                if isinstance(toc_item[1], list):
                    section_title, chapters = toc_item
                    url_title = booktype_slugify(section_title)

                    # let's build a section key and try to get settings for current section
                    section_key = SectionsSettingsPlugin.build_section_key(url_title, sec_count)
                    section_settings = json.loads(settings_dict.get(section_key, '{}'))
                    toc_setting = section_settings.get('toc', {}).get(self.name, '')

                    # jump to next item (continue) if the whole section should be hidden
                    show_in_outputs = section_settings.get('show_in_outputs', {})
                    show_section_in_current_converter = show_in_outputs.get(self.name, True)
                    if not show_section_in_current_converter:
                        continue

                    toc_item = TocItem({
                        'type': 'section',
                        'level': depth,
                        'title': section_title,
                        'url_title': url_title,
                        'show_in_toc': 'hide_section' not in toc_setting
                    })
                    items.append(toc_item)
                    items += _toc(depth + 1, chapters, section_title, toc_setting)
                    sec_count += 1

                # CHAPTERS
                else:
                    chapter_title, chapter_href = toc_item
                    chapter_item = book.get_item_with_href(chapter_href)
                    content = self._get_chapter_content(chapter_item)
                    content = self._fix_horrible_mpdf(content)

                    href_filename, file_extension = os.path.splitext(chapter_href)

                    if not parent:
                        toc_setting = ''

                    toc_item = TocItem({
                        'type': 'chapter',
                        'level': depth,
                        'title': chapter_title,
                        'url_title': booktype_slugify(chapter_title),
                        'href': chapter_href,
                        'href_filename': href_filename,
                        'content': content,
                        'show_in_toc': 'hide_chapters' not in toc_setting
                    })
                    items.append(toc_item)

            return items

        book_toc = _toc(0, self.original_toc_nav)

        data = self._get_data(book)
        data.update(self.get_extra_data(book))
        data.update({
            'book_items': book_toc
        })

        body_name = get_body(self.theme_name, self.name)
        html = render_to_string(body_name, data)
        html_path = os.path.join(self.sandbox_path, self._body_html_name)
        f = codecs.open(html_path, 'wt', 'utf8')
        f.write(html)
        f.close()

    def _write_style(self, book):
        """Creates style file.

        Style file will include default styling, theme styling and custom styling
        provided by the user.

        Created style file will be used by booktype2mpdf.php script
        to create final PDF file.

        :Args:
          - book: EPUB Book object
        """

        if 'settings' not in self.config:
            return

        css_style = create_default_style(self.config, self.name, self.get_extra_style(book))
        theme_style = u''

        if self.theme_name != '':
            theme_style = read_theme_style(self.theme_name, self.name)

            try:
                if self.theme_name == 'custom':
                    custom = self.config['theme'].pop('custom', '{}')
                    custom = json.loads(custom.encode('utf-8'))
                    self.config.update(custom)

                tmpl = template.Template(theme_style)
                _style = tmpl.render(template.Context(self.config))
                theme_style = _style
            except:
                logger.exception("Writing styles failed for `%s` theme." % self.theme_name)

        custom_style = self.config.get('settings', {}).get('styling', u'')

        # add css for fpi
        css_style += self._full_page_images_css

        f = codecs.open('{}/style.css'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(css_style)
        f.write(theme_style)
        f.write(custom_style)
        f.close()

    def _write_configuration(self, book):
        """Creates configuration file for booktype2mpdf.php script.

        Configuration file is read by the booktype2mpdf.php script. It is
        how we pass information to the PHP script which will finally
        create and format the PDF file.

        :Args:
          - book: EPUB Book object
        """

        dc_metadata = self.get_metadata(book)

        data = {'metadata': dc_metadata, 'config': self.config}
        data.update(self.get_extra_configuration())

        f = codecs.open('{}/config.json'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(unicode(json.dumps(data), 'utf8'))
        f.close()

    def _save_images(self, book):
        """Saves all the images from EPUB file to the temporary directory.

        :Args:
          - book: EPUB Book object
        """

        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)

        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            self._save_image(item)

    def _save_image(self, item):
        """Saves single image to the temporary library.

        :Args:
          - item: ebooklib item object
        """

        file_name = os.path.basename(item.file_name)
        file_path = os.path.join(self.images_path, file_name)

        if os.path.exists(file_path):
            file_name = '{}-{}'.format(item.id, file_name)
            file_path = os.path.join(self.images_path, file_name)

        with open(file_path, 'wb') as file:
            file.write(item.content)

        self.images[item.file_name] = file_name

    def _fix_columns(self, content):
        """Add mPDF tags for multi column support.

        :Args:
          - content: lxml node tree with the chapter content

        """
        for column in content.xpath("//div[contains(@class, 'bk-columns')]"):
            column_count = column.get('data-column', '3')
            column_valign = column.get('data-valign', '')
            column_gap = column.get('data-gap', '5')

            columns_start = etree.Element('columns', {
                'column-count': column_count,
                'vAlign': column_valign,
                'column-gap': column_gap
            })

            parent = column.getparent()
            parent.insert(parent.index(column), columns_start)

            if 'bk-marker' not in column.get('class'):
                columns_end = etree.Element('columns', {'column-count': '1'})
                parent.insert(parent.index(column) + 1, columns_end)

            column.drop_tag()

        for column_break in content.xpath("//div[@class='bk-column-break']"):
            column_break.tag = 'columnbreak'
            del column_break.attrib['class']

    def _fix_broken_links(self, content):
        """Removes links from the output and replaces them with textual url.

        :Args:
          - content: lxml node tree with the chapter content

        """

        for link in content.iter('a'):
            if link.attrib.get('href', '') != '':
                text = link.tail or ''
                link.tail = ' [' + link.attrib.get('href', '') + ']' + text
                link.tag = 'span'

    def _fix_content(self, content):
        """Removes unwanted formatting from the content.

        This function will remove links from the content and put
        URL link outside of the link.

        :Args:
          - content: lxml node tree with the chapter content

        :Returns:
          - Returns changed lxml node tree
        """

        if content is None:
            return content

        self._fix_broken_links(content)
        self._fix_columns(content)

        # Fix links to other URL places
        return content

    def _fix_images(self, root, base_path):
        """Fixes links to the images in the content.

        :Args:
          - root: lxml node tree with the content
          - base_path: directory where our images are placed
        """

        for element in root.iter('img'):
            _src = element.get('src', None)

            if _src is None:
                continue
            src_url = urllib2.unquote(_src)
            item_name = os.path.normpath(os.path.join(base_path, src_url))
            try:
                file_name = self.images[item_name]
                element.set('src', self._images_dir + file_name)
            except Exception as e:
                # make sure to delete style attribute to avoid mpdf gets broken
                # TODO: this should be handled from the image editor. Fix it later
                item_style = element.get('style', '')
                if 'transform' in item_style:
                    del element.attrib['style']

                # TODO: discuss what to do in case of missing image

                logger.error(
                    'MPDF::_fix_images: image not found %s (%s)' %
                    (item_name, e)
                )
                continue

    def _fix_full_page_image(self, content):

        # find fpi (full page image) frame
        for img in content.xpath('.//img[contains(@class, "fpi")]'):
            div_image = img.getparent()
            div_group_img = div_image.getparent()

            # remove cpation
            caption = div_group_img.xpath('.//div[@class="caption_small"]')
            if caption:
                div_group_img.remove(caption[0])

            # set id
            fpi_frame_id = "fpi-{}".format(str(uuid.uuid4()))
            div_image.attrib['id'] = fpi_frame_id

            # add fpi end
            div_group_img.insert(div_group_img.index(div_image) + 1,
                                 etree.XML('<div class="fpi-page-end"></div>'))

            # image src
            img = div_image.xpath('.//img')[0]
            fpi_src = img.attrib['src']

            # remove <img/>
            div_image.remove(img)

            # add css for current fpi
            self._full_page_images_css += render_to_string(
                'convert/full_page_image_mpdf.css', {
                    'fpi_id': fpi_frame_id,
                    'fpi_src': fpi_src
                }
            )

            # remove group_img block
            div_group_img.drop_tag()

        return content

    def _get_data(self, book):
        """Returns default data for the front and end matter templates.

        It mainly has default metadata from the book.

        :Returns:
          - Dictionary with default data for the templates
        """

        show_header, show_footer = True, True
        if 'settings' in self.config:
            show_header = self.config['settings'].get('show_header', '') == 'on'
            show_footer = self.config['settings'].get('show_footer', '') == 'on'

        return {
            "title": get_refines(book.metadata, 'title-type', 'main'),
            "subtitle": get_refines(book.metadata, 'title-type', 'subtitle'),
            "shorttitle": get_refines(book.metadata, 'title-type', 'short'),
            "author": get_refines(book.metadata, 'role', 'aut'),

            "publisher": get_metadata(book.metadata, 'publisher'),
            "isbn": get_metadata(book.metadata, 'identifier'),
            "language": get_metadata(book.metadata, 'language'),
            "dir": self.direction,

            "metadata": book.metadata,

            "show_header": show_header,
            "show_footer": show_footer
        }

    def _create_frontmatter(self, book):
        """Creates front matter file.

        Front matter HTML file will be used by booktype2mpdf.php script to create
        PDF file.

        :Args:
          - book: EPUB Book object
        """

        data = self._get_data(book)
        data.update(self.get_extra_data(book))

        frontmatter_name = get_single_frontmatter(self.theme_name, self.name)
        html = render_to_string(frontmatter_name, data)

        f = codecs.open('{}/frontmatter.html'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(html)
        f.close()

    def _create_endmatter(self, book):
        """Creates end matter file.

        End matter HTML file will be used by booktype2mpdf.php script to create
        PDF file.

        :Args:
          - book: EPUB Book object
        """

        data = self._get_data(book)
        data.update(self.get_extra_data(book))

        endmatter_name = get_single_endmatter(self.theme_name, self.name)
        html = render_to_string(endmatter_name, data)

        f = codecs.open('{}/endmatter.html'.format(self.sandbox_path), 'wt', 'utf8')
        f.write(html)
        f.close()

    def _add_theme_assets(self, book):
        """Copy all the assets from the theme to the sandbox directory.

        :Args:
          - book: EPUB book object
        """

        assets = read_theme_assets(self.theme_name, self.name)

        def _write(name, content):
            try:
                os.makedirs('{}/assets/'.format(self.sandbox_path))
            except:
                pass

            if os.path.normpath('{}/assets/{}'.format(self.sandbox_path, name)).startswith(self.sandbox_path):
                try:
                    f = open('{}/assets/{}'.format(self.sandbox_path, name), 'wb')
                    f.write(content)
                    f.close()
                except IOError:
                    pass

        for asset_type, asset_list in assets.iteritems():
            if asset_type == 'images':
                for image_name in asset_list:
                    name = os.path.basename(image_name)
                    content = read_theme_asset_content(self.theme_name, image_name)

                    _write(name, content)
            elif asset_type == 'fonts':
                for font_name in asset_list:
                    name = os.path.basename(font_name)
                    content = read_theme_asset_content(self.theme_name, font_name)

                    _write(name, content)

    def _run_renderer(self, html_path, pdf_path):
        """Calls booktype2mpdf.php script to create PDF file.

        :Args:
          - html_path: path to the html file
          - pdf_path: path to he output PDF file

        :Returns:
          Returns dictionary with output returned by the PHP script
        """

        MPDF_DIR = settings.MPDF_DIR
        PHP_PATH = settings.PHP_PATH
        MPDF_SCRIPT = settings.MPDF_SCRIPT

        params = ['--mpdf={}'.format(MPDF_DIR),
                  '--dir={}'.format(self.sandbox_path),
                  '--output={}'.format(pdf_path)]

        cmd = [PHP_PATH, MPDF_SCRIPT] + params

        try:
            (_, out, err) = utils.run_command(cmd)

            logger.info('MPDF Converter::Stdout: output: "{}", error: "{}"'.format(out, err))

            data = json.loads(out)

            return data
        except Exception as e:
            logger.error(
                'MPDF Converter::Fail running the command "{}".'.format(e))

        return {}

    def _get_theme_mpdf_config(self):
        """
        Checks the theme info.json file and returns the additional options for mpdf
        if there is any defined inside of it.
        """

        profile = self.name
        data = read_theme_info('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, self.theme_name))

        if 'output' in data:
            if profile in data['output']:
                return data['output'][profile].get('options', {})

        return {}
