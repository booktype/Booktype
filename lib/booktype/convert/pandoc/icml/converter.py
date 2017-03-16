import os
import logging

from django.conf import settings

from ...epub.writerplugins import CleanupTagsWriterPlugin
from ...utils import run_command
from ..base_pandoc_converter import BasePandocConverter
from ..writerplugins import RawifiedImagesWriterPlugin


logger = logging.getLogger("booktype.convert.pandoc.icml")


class ICMLConverter(BasePandocConverter):
    """Class for epub to ICML convertion.

       Converter uses epub file as source for pandoc converter.
       It's built on top of :class:`booktype.convert.pandoc.base_pandoc_converter.BasePandocConverter`.
    """

    name = 'icml'

    def _get_plugins(self, epub_book, original_book):
        """Returns the plugins to be used by writer instance"""

        writer_plugin = self._get_writer_plugin(epub_book, original_book)
        rawified_images_writer_plugin = RawifiedImagesWriterPlugin()
        cleanup_tags_writerplugin = CleanupTagsWriterPlugin()

        return [writer_plugin, rawified_images_writer_plugin, cleanup_tags_writerplugin]

    def convert(self, original_book, output_path):
        """
        Creates epub file and convert it to the ZIP with ICML inside.

        :param original_book: Initial epub book object <ebooklib.epub.EpubBook>
        :param output_path: File path to ZIP file with ICML inside
        :return: Dict with output file size
        :raise Exception if convertion failed
        """

        # create epub with raw images
        super(ICMLConverter, self).convert(original_book, output_path)

        # now it's actually epub, not zip, so let's rename to have epub extension
        epub_path = os.path.splitext(output_path)[0] + '.epub'
        os.rename(output_path, epub_path)

        # run sh epub2icml
        self._run_pandoc_converter(epub_path, output_path)

        # remove epub file
        os.remove(epub_path)

        return {"size": os.path.getsize(output_path)}

    def _run_pandoc_converter(self, epub_path, zip_path):
        """Executing epub2icml script to create ZIP with ICML inside.

        :param epub_path: Path to epub file which will be used as source for pandoc convertion
        :param zip_path: Pandoc convertion result file path
        :return: True if convertion was successful
        :raise Exception with pandoc convertion error
        """
        temp_dir = os.path.join(os.path.dirname(epub_path), 'bash_temp')

        try:
            (_, out, err) = run_command(
                'bash {} -i {} -o {} -p {} -t {}'.format(
                    settings.PANDOC_ICML_SCRIPT,
                    epub_path,
                    zip_path,
                    settings.PANDOC_PATH,
                    temp_dir
                ),
                shell=True)
        except Exception as e:
            error = 'PANDOC:ICML Converter::Fail running the command "{}".'.format(e)
            logger.error(error)
            raise Exception(error)

        return True
