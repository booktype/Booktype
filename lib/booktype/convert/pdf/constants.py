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

POINT_2_MM = 25.4 / 72.0
MM_2_POINT = 72.0 / 25.4
INCH_2_POINT = 72

PAGE_EXTREMA = {
    'page_width':  (1, 1000, MM_2_POINT),
    'page_height': (1, 1414, MM_2_POINT),
    'top_margin': (0, 1500, MM_2_POINT),
    'side_margin': (-500, 1500, MM_2_POINT),
    'bottom_margin': (0, 1500, MM_2_POINT),
    'gutter': (-1000, 1000, MM_2_POINT),
    "column_margin": (-1000, 1000, MM_2_POINT),
    "columns": (1, 12, 1),
}

PAGE_SIZE_DATA = {
    'COMICBOOK':      {'page_width': 6.625 * INCH_2_POINT, 'page_height': 10.25 * INCH_2_POINT},
    "POCKET":         {'page_width': 4.25 * INCH_2_POINT, 'page_height': 6.875 * INCH_2_POINT},

    "USLETTER":       {'page_width': 8.5 * INCH_2_POINT, 'page_height': 11 * INCH_2_POINT},
    "USTRADE6x9":     {'page_width': 6 * INCH_2_POINT, 'page_height': 9 * INCH_2_POINT},
    "USTRADE":        {'page_width': 6 * INCH_2_POINT, 'page_height': 9 * INCH_2_POINT},
    "LANDSCAPE9x7":   {'page_width': 9 * INCH_2_POINT, 'page_height': 7 * INCH_2_POINT},
    "SQUARE7.5":      {'page_width': 7.5 * INCH_2_POINT, 'page_height': 7.5 * INCH_2_POINT},
    "ROYAL":          {'page_width': 6.139 * INCH_2_POINT, 'page_height': 9.21 * INCH_2_POINT},
    "CROWNQUARTO":    {'page_width': 7.444 * INCH_2_POINT, 'page_height': 9.681 * INCH_2_POINT},
    "SQUARE8.5":      {'page_width': 8.5 * INCH_2_POINT, 'page_height': 8.5 * INCH_2_POINT},
    "US5.5x8.5":      {'page_width': 5.5 * INCH_2_POINT, 'page_height': 8.5 * INCH_2_POINT},
    "DIGEST":         {'page_width': 5.5 * INCH_2_POINT, 'page_height': 8.5 * INCH_2_POINT},
    "US5x8":          {'page_width': 5 * INCH_2_POINT, 'page_height': 8 * INCH_2_POINT},
    "US7x10":         {'page_width': 7 * INCH_2_POINT, 'page_height': 10 * INCH_2_POINT},

    "Swedish Report": {'page_width': 165 * MM_2_POINT, 'page_height': 242 * MM_2_POINT},
    "UK Report":      {'page_width': 170 * MM_2_POINT, 'page_height': 244 * MM_2_POINT},

    "A5":             {'page_width': 148 * MM_2_POINT, 'page_height': 210 * MM_2_POINT},
    "A4":             {'page_width': 210 * MM_2_POINT, 'page_height': 297 * MM_2_POINT},
    "A3":             {'page_width': 297 * MM_2_POINT, 'page_height': 420 * MM_2_POINT},
    "A2":             {'page_width': 420 * MM_2_POINT, 'page_height': 594 * MM_2_POINT},

    "A1":             {'page_width': 594 * MM_2_POINT, 'page_height': 841 * MM_2_POINT},
    "B5":             {'page_width': 176 * MM_2_POINT, 'page_height': 250 * MM_2_POINT},
    "B4":             {'page_width': 250 * MM_2_POINT, 'page_height': 353 * MM_2_POINT},
    "B3":             {'page_width': 353 * MM_2_POINT, 'page_height': 500 * MM_2_POINT},
    "B2":             {'page_width': 500 * MM_2_POINT, 'page_height': 707 * MM_2_POINT},
    "B1":             {'page_width': 707 * MM_2_POINT, 'page_height': 1000 * MM_2_POINT},

    "UK Tabloid":     {'page_width': 11 * INCH_2_POINT, 'page_height': 17 * INCH_2_POINT},
    "UK Broadsheet":  {'page_width': 18 * INCH_2_POINT, 'page_height': 24 * INCH_2_POINT},
    "US Broadsheet":  {'page_width': 15 * INCH_2_POINT, 'page_height': 22.75 * INCH_2_POINT},
    "Berliner"     :  {'page_width': 315 * MM_2_POINT, 'page_height': 470 * MM_2_POINT},
    "Foolscap (F4)":  {'page_width': 210 * MM_2_POINT, 'page_height': 330 * MM_2_POINT},
    "Oamaru Broadsheet":{'page_width': 382 * MM_2_POINT, 'page_height': 540 * MM_2_POINT},
    "Oamaru Tabloid": {'page_width': 265 * MM_2_POINT, 'page_height': 380 * MM_2_POINT},
}
