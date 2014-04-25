# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
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

import datetime

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import transaction, models

from booktype.apps.core.views import PageView


class RegisterPageView(PageView):
    template_name = "accounts/register.html"
    page_title = _('Register')
    title = _('Please register')

    def get_context_data(self, **kwargs):
        context = super(RegisterPageView, self).get_context_data(**kwargs)

        return context