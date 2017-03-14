from django.template.loader import render_to_string

from booktype.apps.convert import plugin
from booktype.apps.themes.utils import read_theme_style, read_theme_assets

from ..epub.converter import EpubConverter


class BasePandocConverter(EpubConverter):
    """Base class for all pandoc epub based converters.

       Converter uses epub file as source for pandoc converter.
       It's built on top of :class:`booktype.convert.epub.converter.EpubConverter`.
    """
    name = None

    def _get_theme_plugin(self):
        """Return theme plugin

           Theme plugin loads using "epub" key, because we repeat epub convertion.
        """
        return plugin.load_theme_plugin('epub', self.theme_name)

    def _get_theme_style(self):
        """Return selected theme style content

        Theme plugin reads theme using "epub" key, because we repeat epub convertion.
        """
        return read_theme_style(self.theme_name, 'epub')

    def _get_default_style(self):
        """
        Return default epub style content.
        """
        return render_to_string('themes/style_{}.css'.format('epub'), {'dir': self.direction})

    def _get_theme_assets(self):
        """Return theme assets

        Reading theme assets for "epub" file.
        """
        return read_theme_assets(self.theme_name, 'epub')

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
