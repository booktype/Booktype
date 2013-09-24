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

import subprocess

from django.conf import settings


def tidy_cleanup(content, **extra):
    try:
        TIDY_PATH = settings.TIDY_PATH
    except:
        TIDY_PATH = 'tidy'

    cmd = []

    for k, v in extra.iteritems():
        cmd.append('--%s' % k)

        if v:
            cmd.append(v)

    # must parse all other extra arguments
    try:        
        p = subprocess.Popen([TIDY_PATH, '-utf8']+cmd, shell=False, 
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, close_fds=True)
    except OSError:
        return (3, None)
    
    try:
        p.stdin.write(content.encode('utf8'))
    except:
        p.stdin.write(content)


    (cont, p_err) = p.communicate()

    # 0 - all ok
    # 1 - there were warnings
    # 2 - there were errors
    # 3 - exception

    return (p.returncode, cont)
