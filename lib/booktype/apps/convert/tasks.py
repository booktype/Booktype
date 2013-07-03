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

import celery


class Task(celery.Task):
    def __init__(self):
        celery.Task.__init__(self)
        os.putenv("LC_ALL", "en_US.UTF-8")


def task(func):
    """Default decorator for all task functions.
    """
    @celery.task(base = Task, name = func.__name__)
    def decorated_func(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return decorated_func


@task
def convert_one(profile, config, book, output):
    result = {
        "status" : "ok",
    }
    return result


@task
def convert(request_data):
    result = {
        "status" : "ok",
    }
    return result


__all__ = ("convert", "convert_one", )
