from ..epub.converter import Epub3Converter


class BasePandocConverter(Epub3Converter):
    """Base class for all pandoc epub based converters.

       Converter uses epub file as source for pandoc converter.
       It's built on top of :class:`booktype.convert.epub.converter.Epub3Converter`.
    """
    name = None

    def _run_pandoc_converter(self, epub_path, zip_path):
        """
        Executing pandoc convertion after epub was created.
        In most cases this method will be executed in :func:`self.convert`.
        :param epub_path: Path to epub file which will be used as source for pandoc convertion
        :param zip_path: Pandoc convertion result file path
        :return: True if convertion was successful
        :raise Exception with pandoc convertion error
        """
        raise NotImplementedError
