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

import json

from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.staticfiles.templatetags.staticfiles import static

from booktype.apps.core.templatetags.booktype_tags import jsonlookup

register = template.Library()

ACTIVITY_KIND_VERBOSE = {
    1: _("Created new chapter"),
    2: _("Chapter saved"),
    3: _("Chapter rename"),
    4: _("Chapter reorder"),
    5: _("Split chapter"),
    6: _("Created new section"),
    7: _("Renamed section"),
    10: _("Created new book"),
    11: _("Minor version"),
    12: _("Major version"),
    13: _("Uploaded"),
    14: _("Attachment delete"),
    16: _("Upload cover"),
    18: _("Cover update"),
    19: _("Delete chapter"),
    20: _("Delete section")
}


@register.assignment_tag
def verbose_activity(activity):
    """
    Template tag to check what kind of activity is the one coming
    as paramenter and then append some useful verbose and user frield
    fields to it.
    """

    verbose = unicode(ACTIVITY_KIND_VERBOSE.get(activity.kind, None))
    default_image = static('core/img/chapter-default.png')
    link_url = None
    book = activity.book
    book_version = book.version.get_version()

    if verbose:
        # get the right image for activity
        if activity.kind == 6:
            default_image = static('core/img/section-default.png')

        if activity.kind == 4:
            default_image = static('core/img/reorder.png')

        # get chapter link
        if activity.chapter:
            link_text = activity.chapter.title
            link_url = reverse(
                'reader:draft_chapter_page',
                args=[book.url_title, book_version, activity.chapter.url_title]
            )

        if activity.kind in [4, 10]:
            link_text = book.title
            link_url = reverse(
                'reader:infopage',
                args=[book.url_title]
            )

        if activity.kind == 13:
            link_text = filename = jsonlookup(activity.args, 'filename')
            link_url = reverse(
                'reader:draft_attachment',
                args=[book.url_title, book_version, filename]
            )

        # show more info when cover update
        if activity.kind == 18:
            link_text = jsonlookup(activity.args, 'title')
            link_url = '{}#covers'.format(reverse('edit:editor', args=[book.url_title]))

        activity_dict = dict(
            verbose=verbose,
            image_url=default_image,
            modified=activity.modified,
            user=activity.user,
            book=book,
            kind=activity.kind
        )

        if link_url:
            activity_dict['link_url'] = link_url
            activity_dict['link_text'] = '%s' % link_text

        if 'link_text' not in activity_dict and activity.kind != 4:
            try:
                activity_dict['link_text'] = json.loads(activity.args).values()[0]
            except:
                activity_dict['link_text'] = ''

        return activity_dict

    else:
        return {}
