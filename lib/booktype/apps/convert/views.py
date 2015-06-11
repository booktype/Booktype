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
import json
import uuid
import celery
import sputnik

from django.views.generic.base import View
from django.http import HttpResponse, Http404
from django.conf import settings

from booktype.apps.loadsave.utils import RestrictExport

from . import tasks
from .utils.uploadhandler import FileUploadHandler


class OutputData(object):
    """Encapsulates information for a single conversion output."""

    def __init__(self, data):
        self.profile = data["profile"]
        self.output = data["output"]
        self.config = data.get("config", {})


class RequestData(object):
    """Encapsulates all information specified by the conversion request."""

    @classmethod
    def parse(klass, text):
        return klass(json.loads(text))

    def __init__(self, data):
        self.assets = data.get("assets", {})  # TODO: check type is dict
        self.input = data["input"]
        self.outputs = {
            k: OutputData(v) for (k, v) in data["outputs"].iteritems()
        }


class ConvertView(RestrictExport, View):

    def post(self, request):
        token = str(uuid.uuid1())

        # sandbox directory for this request
        base_path = os.path.join(settings.MEDIA_ROOT, "tmp", token)
        os.makedirs(base_path)

        request.upload_handlers = (FileUploadHandler(base_path), )

        # parse the request
        request_spec = get_request_spec(request)
        request_data = RequestData.parse(request_spec)

        # name:path for all uploaded files
        request_data.files = {
            field_name: _file.file_path()
            for (field_name, _file) in request.FILES.iteritems()
        }

        # start the task in the background
        async_result = tasks.convert.apply_async((request_data, base_path))
        task_id = map_task_id(async_result.task_id, token)

        response_data = {
            "state": async_result.state,
            "task_id": task_id,
        }
        return HttpResponse(json.dumps(response_data),
                            content_type="application/json")

    def get(self, request, task_id):
        task_id = sputnik.rcon.get("convert:task_id:" + task_id)

        if task_id is None:
            raise Http404

        def get_task_name(async_result):
            return async_result.task_id.split(':')[0]

        async_result = celery.current_app.AsyncResult(task_id)
        task_info = get_task_info(async_result)
        task_result = task_info.get("result")
        if task_result:
            task_info["result"] = {
                get_task_name(subtask): get_task_info(subtask)
                for (_n, subtask) in task_result.iteritems()
            }

        response_data = task_info

        return HttpResponse(json.dumps(response_data),
                            content_type="application/json")


def get_task_info(async_result):
    status = {"state": async_result.state}
    if async_result.failed():
        status["error"] = str(async_result.result)
    elif async_result.result is not None:
        status["result"] = async_result.result
    return status


def get_request_spec(request):
    if request.POST:
        return request.POST["request-spec"]
    else:
        return request.body


def map_task_id(task_id, token):
    sputnik.rcon.set("convert:task_id:" + token, task_id)
    return token


def get_task_id(token):
    return sputnik.rcon.get("convert:task_id:" + token)


__all__ = ("ConvertView", )
