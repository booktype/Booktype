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

import celery
import celery.result

from django.views.generic.base import View
from django.http import HttpResponse, Http404

from django.utils import simplejson as json

from booki.utils import log

from . import tasks


class OutputData(object):
    """Encapsulates information for a single conversion output."""

    def __init__(self, data):
        self.profile = data["profile"]
        self.config  = data["config"]
        self.output  = data["output"]


class RequestData(object):
    """Encapsulates all information specified by the conversion request."""

    @classmethod
    def parse(klass, text):
        return klass(json.loads(text))

    def __init__(self, data):
        self.book = data["book"]
        self.outputs = {k: OutputData(v) for (k,v) in data["outputs"].iteritems()}


class ConvertView(View):
    def post(self, request):
        request_data = RequestData.parse(request.body)
        async_result = tasks.convert.apply_async((request_data,))
        response_data = {
            "state"   : async_result.state,
            "task_id" : async_result.task_id,
        }
        return HttpResponse(json.dumps(response_data), mimetype="application/json")

    def get(self, request, task_id):
        async_result = celery.current_app.AsyncResult(task_id)
        #if async_result.task_name != tasks.convert.name:
        #    raise Http404
        response_data = {
            "state"   : async_result.state,
            "result"  : str(async_result.result),
        }
        return HttpResponse(json.dumps(response_data), mimetype="application/json")


__all__ = ("ConvertView", )
