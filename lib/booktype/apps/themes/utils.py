import os
import json
import codecs
import logging

from django.conf import settings

logger = logging.getLogger("booktype.convert")


def get_body(theme_name, profile):
    """Returns file name for the template.

    User defined themes could have specific front matter. We will check theme configuration
    if body is defined. If it is not defined, we will return default template file name.

    :Args:
      - theme_name: Name of the theme
      - profile: Output profile (e.g. mpdf, screenpdf)

    :Returns:
      Returns file name for the template.
    """

    data = read_theme_info('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, theme_name))

    if 'output' in data:
        if profile in data['output']:
            if 'body' in data['output'][profile]:
                return 'themes/{}/{}'.format(theme_name, data['output'][profile]['body'])

    return u'themes/body_{}.html'.format(profile)


def get_single_frontmatter(theme_name, profile):
    """Returns file name for the template.

    User defined themes could have specific front matter. We will check theme configuration
    if front matter is defined. If it is not defined, we will return default template file name.

    :Args:
      - theme_name: Name of the theme
      - profile: Output profile (e.g. mpdf, screenpdf)

    :Returns:
      Returns file name for the template.
    """

    data = read_theme_info('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, theme_name))

    if 'output' in data:
        if profile in data['output']:
            if 'frontmatter' in data['output'][profile]:
                return 'themes/{}/{}'.format(theme_name, data['output'][profile]['frontmatter'])

    return u'themes/frontmatter_{}.html'.format(profile)


def get_single_endmatter(theme_name, profile):
    """Returns file name for the template.

    User defined themes could have specific end matter. We will check theme configuration
    if end matter is defined. If it is not defined, we will return default template file name.

    :Args:
      - theme_name: Name of the theme
      - profile: Output profile (e.g. mpdf, screenpdf)

    :Returns:
      Returns file name for the template.
    """

    data = read_theme_info('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, theme_name))

    if 'output' in data:
        if profile in data['output']:
            if 'endmatter' in data['output'][profile]:
                return 'themes/{}/{}'.format(theme_name, data['output'][profile]['endmatter'])

    return u'themes/endmatter_{}.html'.format(profile)


def read_theme_style(theme_name, profile):
    """Returns content of the CSS file for defined theme.

    :Args:
      - theme_name: Name of the theme
      - profile: Output profile (e.g. mpdf, screenpdf, epub, mobi)

    :Returns:
      Content of the CSS file defined for that theme.
    """
    theme_style = u''

    # todo
    # if custom, also generate custom stuff
    if os.path.isdir('{}/themes/{}/'.format(settings.BOOKTYPE_ROOT, theme_name)):
        style_file = '{}/themes/{}/{}.css'.format(settings.BOOKTYPE_ROOT, theme_name, profile)
        if os.path.exists(style_file):
            f = codecs.open(style_file, 'rt', 'utf8')
            theme_style = f.read()
            f.close()

    return theme_style


def read_theme_assets(theme_name, profile):
    """Returns dictionary with a list of assets.

    :Args:
      - theme_name: Name of the theme
      - profile: Output profile (e.g. mpdf, screenpdf, epub, mobi)

    :Returns:
      Dictionary with a list of assets.
    """

    data = read_theme_info('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, theme_name))

    if 'output' in data:
        if profile in data['output']:
            if 'assets' in data['output'][profile]:
                return data['output'][profile]['assets']

    return {}


def read_theme_asset_content(theme_name, file_name):
    """Read content of an asset.

    :Args:
      - theme_name: Name of the theme
      - file_name: Asset file name

    :Returns:
      Raw content.
    """
    file_name = '{}/themes/{}/{}'.format(settings.BOOKTYPE_ROOT, theme_name, file_name)
    base_dir = '{}/themes/{}/'.format(settings.BOOKTYPE_ROOT, theme_name)

    if os.path.exists(file_name):
        if os.path.normpath(file_name).startswith(base_dir):
            try:
                f = file(file_name, 'rb')
                return f.read()
            except IOError:
                return None

    return None


def read_theme_info(file_path):
    data = {}

    try:
        f = codecs.open(file_path, 'r', 'utf8')
        data = json.loads(f.read())
    except:
        logger.exception('Could not read theme info file.')

    return data
