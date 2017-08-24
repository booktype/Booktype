import os
import logging
from unipath import Path

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from booktype.convert.image_editor_conversion import ImageEditorConversion
from booktype.constants import EPUB_DOCUMENT_WIDTH

from ...utils import run_command
from ..base_pandoc_converter import BasePandocConverter


logger = logging.getLogger("booktype.convert.pandoc.docx")


class DOCXConverter(BasePandocConverter):
    """Class for epub to DOCX convertion.

       Converter uses epub file as source for pandoc converter.
       It's built on top of :class:`booktype.convert.pandoc.base_pandoc_converter.BasePandocConverter`.
    """

    name = 'docx'
    verbose_name = _('Word (DOCX)')
    support_section_settings = True

    def pre_convert(self, original_book, book):
        super(DOCXConverter, self).pre_convert(original_book, book)

        self._bk_image_editor_conversion = ImageEditorConversion(
            original_book, EPUB_DOCUMENT_WIDTH, self
        )

    def convert(self, original_book, output_path):
        """
        Creates epub file and convert it to the ZIP with DOCX inside.

        :param original_book: Initial epub book object <ebooklib.epub.EpubBook>
        :param output_path: File path to ZIP file with DOCX inside
        :return: Dict with output file size
        :raise Exception if convertion failed
        """
        # create epub
        super(DOCXConverter, self).convert(original_book, output_path)

        # now it's actually epub, not zip, so let's rename to have epub extension
        epub_path = os.path.splitext(output_path)[0] + '.epub'
        os.rename(output_path, epub_path)

        # run sh epub2docx
        self._run_pandoc_converter(epub_path, output_path)

        # remove epub file
        os.remove(epub_path)

        return {"size": os.path.getsize(output_path)}

    def _run_pandoc_converter(self, epub_path, zip_path):
        """Executing epub2docx script to create ZIP with DOCX inside.

        :param epub_path: Path to epub file which will be used as source for pandoc convertion
        :param zip_path: Pandoc convertion result file path
        :return: True if convertion was successful
        :raise Exception with pandoc convertion error
        """
        temp_dir = os.path.join(os.path.dirname(epub_path), 'bash_temp')

        BK_LIB_ROOT = Path(os.path.abspath(__file__)).ancestor(6)
        default_path = '{}/scripts/epub2docx.sh'.format(BK_LIB_ROOT)
        script_path = getattr(settings, 'PANDOC_DOCX_SCRIPT', default_path)

        try:
            (_, out, err) = run_command(
                'bash {} -i {} -o {} -p {} -t {}'.format(
                    script_path,
                    epub_path,
                    zip_path,
                    settings.PANDOC_PATH,
                    temp_dir
                ),
                shell=True)
        except Exception as e:
            error = 'PANDOC:DOCX Converter::Fail running the command "{}".'.format(e)
            logger.error(error)
            raise Exception(error)

        return True
