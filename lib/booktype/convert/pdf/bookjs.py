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

import tempfile
import logging

from . import constants
from .. import utils


logger = logging.getLogger("booktype.convert.pdf")


def render(html_path, pdf_path, **kwargs):
    """Creates a book PDF from the provided HTML document.
    """
    program = "renderer"

    params = [
        #"-platform", "xcb",
        "-output", pdf_path,
    ]

    if kwargs.has_key("page_config"):
        params += ["-page-config", kwargs.get("page_config")]

    custom_css_file = None
    custom_css_text = kwargs.get("custom_css")
    if custom_css_text:
        custom_css_file = tempfile.NamedTemporaryFile(prefix="renderer-", suffix=".css", delete=True)
        custom_css_file.write(custom_css_text)
        custom_css_file.flush()
        params += ["-custom-css", custom_css_file.name]

    cmd = [ program ] + params + [ html_path ]

    try:
        utils.run_command(cmd)
    finally:
        if custom_css_file:
            custom_css_file.close()


def make_pagination_config(args):
    """Creates pagination config. text using page setting arguments.
    """
    page_settings = _get_page_settings(args)

    # NOTE: size values from page settings are always in "points"

    page_width    = page_settings.get("page_width",    420) # A
    page_height   = page_settings.get("page_height",   595) # 5
    top_margin    = page_settings.get("top_margin",    0.8 * 72)
    bottom_margin = page_settings.get("bottom_margin", 0.8 * 72)
    side_margin   = page_settings.get("side_margin",   0.5 * 72)
    gutter        = page_settings.get("gutter",        0.8 * 72)

    def unit(x):
        # Convert from points (pt) to whatever is specified by lengthUnit.
        # Division by 0.75 is because of a bug currently present in the
        # renderer using pt as device pixel instead of px.
        return x / 72.0 / 0.75

    config = {
        "lengthUnit"  : "in",
        "pageWidth"   : unit(page_width),
        "pageHeight"  : unit(page_height),
        "outerMargin" : unit(side_margin),
        "innerMargin" : unit(gutter),
        "contentsTopMargin"    : unit(top_margin),
        "contentsBottomMargin" : unit(bottom_margin),
    }

    items = ["%s:%s" % (key,repr(val)) for key,val in config.items()]
    text = ",".join(items)

    return text


def _get_page_settings(args):
    settings = {}

    for key, (min_val, max_val, multiplier) in constants.PAGE_EXTREMA.iteritems():
        if not args.has_key(key):
            continue

        val = float(args.get(key))

        if val < min_val or val > max_val:
            logger.error('rejecting %s: outside %s' % (val, extrema))
        else:
            settings[key] = val * multiplier

    if args.has_key("page_size"):
        page_size = args.get("page_size")

        if constants.PAGE_SIZE_DATA.has_key(page_size):
            settings.update(constants.PAGE_SIZE_DATA.get(page_size))
        else:
            raise ValueError("invalid page size specifier")

    return settings
