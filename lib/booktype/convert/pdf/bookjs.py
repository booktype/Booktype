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
import subprocess

import logging


logger = logging.getLogger("booktype.convert")


def run(cmd):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except Exception:
        logger.error("Failed on command: %r" % cmd)
        raise
    logger.debug("%s\n%s returned %s and produced\nstdout:%s\nstderr:%s" %
        (' '.join(cmd), cmd[0], p.poll(), out, err))
    return p.poll()


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
        run(cmd)
    finally:
        if custom_css_file:
            custom_css_file.close()
