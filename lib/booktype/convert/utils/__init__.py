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

import os

import logging
import subprocess


logger = logging.getLogger("booktype.convert")


def run_command(cmd, shell=False):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        out, err = p.communicate()

        if err:
            log_cmd = cmd
            if cmd.__class__ == list:
                log_cmd = ' '.join(cmd)

            logger.error("Error while running the command. Error: {0}. Command: {1}".format(err, log_cmd))

    except Exception:
        logger.error("Error while running the command: %r" % cmd)
        raise

    logger.debug("%s\n%s returned %s and produced\nstdout:%s\nstderr:%s" %
        (' '.join(cmd), cmd[0], p.poll(), out, err))

    return (p.poll(), out, err)
