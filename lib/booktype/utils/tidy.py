# This file is part of Booktype.
# Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import logging
import subprocess

from django.conf import settings

logger = logging.getLogger('booktype.utils.tidy')


def tidy_cleanup(content, **extra):
    """
    Function that wraps tidy html command. It also uses our custom
    booktype.utils.misc.remove_unknown_tags function to avoid issues when
    sending the content to the external command

    Args:
        - content `(str)`: HTML string content

    Returns:
        - cleaned html content
    """
    from . import misc

    TIDY_PATH = getattr(settings, 'TIDY_PATH', 'tidy')
    cmd = []

    content = misc.remove_unknown_tags(content)

    for k, v in extra.iteritems():
        cmd.append('--%s' % k)

        if v:
            cmd.append(v)

    # must parse all other extra arguments
    try:
        p = subprocess.Popen(
                [TIDY_PATH, '-utf8'] + cmd, shell=False,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True
            )
    except OSError:
        return (3, None)

    try:
        try:
            decoded_content = content.decode('utf-8')
        except UnicodeDecodeError:
            decoded_content = content.decode('ascii')
        p.stdin.write(decoded_content.encode('utf-8'))
    except Exception as err:
        logger.warn("TidyCleanup: There was an error when encoding content. Using raw content. %s" % err)
        p.stdin.write(content)

    (cont, p_err) = p.communicate()

    if len(cont) == 0:
        logger.warn("TidyCleanup Attention: None value was provided as content \
            Now trying to clean up content with lxml")

    # 0 - all ok
    # 1 - there were warnings
    # 2 - there were errors
    # 3 - exception

    return (p.returncode, cont)
