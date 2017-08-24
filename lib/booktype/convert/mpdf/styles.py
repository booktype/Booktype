# This file is part of Booktype.
# Copyright (c) 2015 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

from django.template.loader import render_to_string

from booktype.utils import config


CROP_MARGIN = 18


def get_page_size(conf):
    """Returns page number in millimeters.

    Page size is defined in the constant file but user is able to define custom
    page sizes in the settings file. We will try to find custom page size, if
    it is not found we will check for the default page sizes.

    :Args:
      - conf: Dictionary with all the output settings

    :Returns:
      Returns tuple with width and height values for the page size.
    """

    page_size = conf.get('size', 'default')

    if page_size == 'custom':
        return int(round(float(conf['custom_width']))), int(round(float(conf['custom_height'])))

    PAGE_SIZE_DATA = config.get_configuration('PAGE_SIZE_DATA')

    # We need size in millimieters and some of the values in
    # configuration are floats. Just round them and return them
    # as integers.
    sze = PAGE_SIZE_DATA.get(page_size.lower(), (100, 100))

    return int(round(sze[0])), int(round(sze[1]))


def get_value(sett, name):
    """Get value from the settings dictionary.

    At the moment this could be achieved with simple get method but
    we are thinking there might be some more logic in the future some
    better have our own function for this.
    """

    return sett.get(name, 0)


def create_default_style(config, name, extra = {}):
    """We create CSS file with the default options.

    :Args:
      - config: Settings options send by the user
      - name: Name of the output profile
      - extra: Extra options

    :Returns:
      Returns content of the CSS file as a string.
    """

    width, height = get_page_size(config['settings'])

    if 'crop_marks' in config['settings']:
        crop_marks = config['settings']['crop_marks'] == 'on'
    else:
        crop_marks = False

    get_value(config['settings'], 'top_margin')

    data = {'page_width': width,
        'page_height': height,
        'page_width_bleed': config['page_width_bleed'],
        'page_height_bleed': config['page_height_bleed'],
        'crop_marks': crop_marks,
        'top_margin': get_value(config['settings'], 'top_margin'),
        'bottom_margin': get_value(config['settings'], 'bottom_margin'),
        'side_margin': get_value(config['settings'], 'side_margin'),
        'gutter': get_value(config['settings'], 'gutter'),
        'header_margin': get_value(config['settings'], 'header_margin'),
        'footer_margin': get_value(config['settings'], 'footer_margin'),
        'show_header': get_value(config['settings'], 'show_header') == 'on',
        'show_footer': get_value(config['settings'], 'show_footer') == 'on',
        }
    data.update(extra)

    return render_to_string('themes/style_{}.css'.format(name), data)
