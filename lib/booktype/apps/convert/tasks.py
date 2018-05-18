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
import celery.result
import logging

from uuid import uuid4
from celery import group
from celery.result import allow_join_result

from booktype.convert import loader
from booktype.convert.runner import run_conversion
from booktype.convert.assets import AssetCollection

from . import utils


logger = logging.getLogger("booktype.apps.convert")


class Task(celery.Task):
    def __init__(self):
        celery.Task.__init__(self)
        os.putenv("LC_ALL", "en_US.UTF-8")
        self.converters = loader.find_all(
            module_names=utils.get_converter_module_names())


def task(func):
    """
    Default decorator for all task functions.
    """
    @celery.task(base=Task, name=func.__name__)
    def decorated_func(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    return decorated_func


@task
def convert_one(*args, **kwargs):
    """Runs one conversion with the specified arguments."""

    def callback(meta):
        celery.current_task.update_state(state="PROGRESS", meta=meta)

    kwargs.update({
        "converters": celery.current_task.converters,
        "callback": callback,
    })

    result = run_conversion(*args, **kwargs)

    result.update({
        "output": utils.path2url(result["output"]),
    })

    return result


@task
def convert(request_data, base_path):
    """
    Converts the given assets into outputs desired formats. It receives
    a dictionary request_data with something like this:
        {
            "input": "testbook.epub",
            "assets": {
                "testbook.epub": "http://127.0.0.1:8000/bla-foo/_export/"
            },
            "outputs": {
                "two": {
                    "profile": "epub",
                    "output": "testbook.epub",
                    "config": {
                        "project_id": "bla-foo"
                    }
                }
            }
        }
    """

    # TODO we should use a chain of tasks

    assets = AssetCollection(base_path)

    assets.add_urls(request_data.assets)
    assets.add_files(request_data.files)

    subtasks = []
    for (name, output) in request_data.outputs.iteritems():
        sandbox_path = os.path.join(base_path, name)
        output_path = os.path.join(sandbox_path, output.output)

        subtask_args = (output.profile, request_data.input, output_path)
        subtask_kwargs = {
            "assets": assets,
            "config": output.config,
            "sandbox_path": sandbox_path
        }

        custom_task_id = '%s:%s' % (name, str(uuid4()))
        subtask = convert_one.subtask(
            args=subtask_args,
            kwargs=subtask_kwargs,
            task_id=custom_task_id
        )
        subtasks.append(subtask)

    job = group(subtasks, disable_sync_subtasks=False)
    result = job.apply_async()

    # TODO we should use chain here
    # http://docs.celeryq.org/en/latest/userguide/tasks.html#task-synchronous-subtasks
    with allow_join_result():
        result.join(propagate=False)

    subtasks_info = {async.task_id: async for async in result.children}
    celery.current_task.update_state(state="PROGRESS", meta=subtasks_info)

    return subtasks_info


__all__ = ("convert", )
