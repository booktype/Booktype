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

INCH_TO_MM = 25.4

CROP_MARGIN = 18

PAGE_SIZE_DATA = {
    'comicbook':      (6.625 * INCH_TO_MM, 10.25 * INCH_TO_MM),
    "pocket":         (4.25 * INCH_TO_MM, 6.875 * INCH_TO_MM),
    "usletter":       (8.5 * INCH_TO_MM, 11 * INCH_TO_MM),
    "ustrade6x9":     (6 * INCH_TO_MM, 9 * INCH_TO_MM),
    "ustrade":        (6 * INCH_TO_MM, 9 * INCH_TO_MM),
    "landscape9x7":   (9 * INCH_TO_MM, 7 * INCH_TO_MM),
    "square7.5":      (7.5 * INCH_TO_MM, 7.5 * INCH_TO_MM),
    "royal":          (6.139 * INCH_TO_MM, 9.21 * INCH_TO_MM),
    "crownquarto":    (7.444 * INCH_TO_MM, 9.681 * INCH_TO_MM),
    "square8.5":      (8.5 * INCH_TO_MM, 8.5 * INCH_TO_MM),
    "us5.5x8.5":      (5.5 * INCH_TO_MM, 8.5 * INCH_TO_MM),
    "digest":         (5.5 * INCH_TO_MM, 8.5 * INCH_TO_MM),
    "us5x8":          (5 * INCH_TO_MM, 8 * INCH_TO_MM),
    "us7x10":         (7 * INCH_TO_MM, 10 * INCH_TO_MM),
    "a5":             (148, 210),
    "a4":             (210, 297),
    "a3 (nz tabloid)": (297, 420),
    "a2 (nz broadsheet)": (420, 594),
    "a1":             (594, 841),
    "b5":             (176, 250),
    "b4":             (250, 353),
    "b3":             (353, 500),
    "b2":             (500, 707),
    "b1":             (707, 1000),

    # Not so sure about next 3
    "uk tabloid":     (11 * INCH_TO_MM, 17 * INCH_TO_MM),
    "uk broadsheet":  (18 * INCH_TO_MM, 24 * INCH_TO_MM),
    "us broadsheet":  (15 * INCH_TO_MM, 22.75 * INCH_TO_MM),

    "berliner"     :  (315, 470),
    "foolscap (f4)":  (210, 330),
    "oamaru broadsheet" :(382, 540),
    "oamaru tabloid": (265, 380),
}                      


def get_page_size(config):
    page_size = config.get('size', 'default')

    if page_size == 'custom':
        return config['custom_width'], config['custom_height']

    return PAGE_SIZE_DATA.get(page_size.lower(), (100, 100))


def get_value(sett, name):
    return sett.get(name, 0)

def create_default_style(config, name, extra = {}):
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
        'footer_margin': get_value(config['settings'], 'footer_margin')
        }
    data.update(extra)

    return render_to_string('convert/style_{}.css'.format(name), data)
