# This file is part of Booktype.
# Copyright (c) 2014 Helmy Giacoman <helmy.giacoman@sourcefabric.org>
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

from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.staticfiles.templatetags.staticfiles import static

from booki.editor.templatetags.booki_tags import jsonlookup

register = template.Library()

ACTIVITY_KIND_VERBOSE = {
    1:  _("Created new chapter"),
    2:  _("Chapter saved"),
    3:  _("Chapter rename"),
    4:  _("Chapter reorder"),
    5:  _("Split chapter"),
    6:  _("Created new section"),
    10: _("Created new book"),
    11: _("Minor version"),
    12: _("Major version"),
    13: _("Uploaded"),
    14: _("Attachment delete"),
    16: _("Upload cover"),
    19: _("Delete chapter")
}

@register.assignment_tag
def verbose_activity(activity):
    # TODO: add docstrings here

    verbose = ACTIVITY_KIND_VERBOSE.get(activity.kind, None)
    default_image = static('core/img/chapter-default.png')
    link_url = None
    book = activity.book
    book_version = book.version.get_version()
    
    if verbose:
        title = verbose

        # get the right image for activity
        if activity.kind == 6:
            default_image = static('core/img/section-default.png')

        if activity.kind == 4:
            default_image = static('core/img/reorder.png')

        # get chapter link
        if activity.chapter:
            link_text = activity.chapter.title
            link_url = reverse(
                'draft_chapter', 
                args=[book.url_title, book_version, activity.chapter.url_title]
            )

        if activity.kind == 10:
            link_text = book.title
            link_url = '.'

        if activity.kind == 13:
            link_text = filename = jsonlookup(activity.args, 'filename')
            link_url = reverse(
                'draft_attachment',
                args=[book.url_title, book_version, filename]
            )

        activity_dict = dict(verbose=verbose, image_url=default_image)
        if link_url:
            activity_dict['link_url'] = link_url
            activity_dict['link_text'] = '"%s"' % link_text

        return activity_dict

    else:
        return {}