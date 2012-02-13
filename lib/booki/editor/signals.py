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

import django.dispatch


book_created = django.dispatch.Signal(providing_args=["book"])
book_version_created = django.dispatch.Signal(providing_args=["book", "version"])

chapter_created = django.dispatch.Signal(providing_args=["chapter"])
chapter_modified = django.dispatch.Signal(providing_args=["user", "chapter"])

attachment_uploaded = django.dispatch.Signal(providing_args=["attachment"])

book_toc_changed = django.dispatch.Signal()


