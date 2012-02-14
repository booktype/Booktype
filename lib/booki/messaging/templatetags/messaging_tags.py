# This file is part of Booktype.
# Copyright (c) 2012  Seravo Oy <tuukka@seravo.fi>
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

import random

from django.conf import settings

from django import template

from itertools import chain

from booki.messaging.models import Post, PostAppearance, Endpoint, Following
from django.contrib.auth import models as auth_models

from booki.messaging.views import get_endpoint_or_none

register = template.Library()

### timelines:

@register.inclusion_tag("messaging/timeline.html")
def user_timeline(username):
    endpoint = get_endpoint_or_none("@"+username)

    posts_by_user = Post.objects.filter(sender=endpoint).order_by("-timestamp")

    appearances = PostAppearance.objects.filter(endpoint=endpoint)
    user_posts = (x.post for x in appearances.order_by("-timestamp"))

    posts = sorted(chain(posts_by_user, user_posts), key=lambda x:x.timestamp,
                   reverse=True)

    return dict(syntax="@"+username, posts=posts,
                DATA_URL=settings.DATA_URL)

@register.inclusion_tag("messaging/timeline.html")
def group_timeline(groupname):
    endpoint = get_endpoint_or_none("!"+groupname)
    appearances = PostAppearance.objects.filter(endpoint=endpoint)
    group_posts = (x.post for x in appearances.order_by("-timestamp"))
    return dict(syntax="!"+groupname, posts=group_posts)

@register.inclusion_tag("messaging/timeline.html")
def book_timeline(bookname):
    endpoint = get_endpoint_or_none(u"\u212c"+bookname)
    appearances = PostAppearance.objects.filter(endpoint=endpoint)
    book_posts = (x.post for x in appearances.order_by("-timestamp"))
    return dict(syntax=u"\u212c"+bookname, posts=book_posts)

@register.inclusion_tag("messaging/timeline.html")
def tag_timeline(tagname):
    endpoint = get_endpoint_or_none("#"+tagname)
    appearances = PostAppearance.objects.filter(endpoint=endpoint)
    tag_posts = (x.post for x in appearances.order_by("-timestamp"))
    return dict(syntax="#"+tagname, posts=tag_posts)

### messagefields:
@register.inclusion_tag("messaging/messagefield.html", takes_context=True)
def user_messagefield(context, username):
    return dict(syntax="@"+username+" " if username else "",
                request=context.get('request'),
                random=random.getrandbits(60)
                )

@register.inclusion_tag("messaging/messagefield.html", takes_context=True)
def group_messagefield(context, groupname):
    return dict(syntax="!"+groupname+" ",
                request=context.get('request'),
                random=random.getrandbits(60)
                )

@register.inclusion_tag("messaging/messagefield.html", takes_context=True)
def book_messagefield(context, bookname):
    return dict(syntax=u"\u212c"+bookname+" ",
                request=context.get('request'),
                random=random.getrandbits(60)
                )

@register.inclusion_tag("messaging/messagefield.html", takes_context=True)
def tag_messagefield(context, tagname):
    return dict(syntax=u"#"+tagname+" ",
                request=context.get('request'),
                random=random.getrandbits(60)
                )

@register.inclusion_tag("messaging/messagefield.html", takes_context=True)
def messagefield(context, syntax):
    return dict(syntax=syntax+" ",
                request=context.get('request'),
                random=random.getrandbits(60)
                )

@register.inclusion_tag("messaging/messagefield_button.html", takes_context=True)
def messagefield_button(context):
    return dict(request=context.get('request'),
                random=random.getrandbits(60))

### stalking:

@register.inclusion_tag("messaging/followingbox.html")
def user_followingbox(username):
    user = get_endpoint_or_none(syntax="@"+username)
    followings = Following.objects.filter(follower=user)
    target_users = (following.target.syntax[1:] for following in followings if following.target.syntax.startswith("@"))
    return dict(target_users=target_users)

@register.inclusion_tag("messaging/followersbox.html")
def user_followersbox(username):
    endpoint = get_endpoint_or_none(syntax="@"+username)
    followings = Following.objects.filter(target=endpoint)
    followers = (following.follower.syntax[1:] for following in followings)
    return dict(followers=followers)

@register.inclusion_tag("messaging/tags.html")
def user_tagbox(username):
    user = get_endpoint_or_none(syntax="@"+username)
    followings = Following.objects.filter(follower=user)
    tags = (following.target.syntax[1:] for following in followings if following.target.syntax.startswith("#"))
    books = (following.target.syntax[1:] for following in followings if following.target.syntax.startswith(u"\u212c"))
    return dict(tags=tags, books=books)

@register.inclusion_tag("messaging/user_followbutton.html")
def user_followbutton(username, requestuser):
    return dict(username=username,
                alreadyfollowing=bool(Following.objects.filter(follower=get_endpoint_or_none("@"+requestuser), target=get_endpoint_or_none("@"+username))))

@register.inclusion_tag("messaging/book_followbutton.html")
def book_followbutton(bookname, requestuser):
    return dict(bookname=bookname,
                alreadyfollowing=bool(Following.objects.filter(follower=get_endpoint_or_none("@"+requestuser), target=get_endpoint_or_none(u"\u212c"+bookname))))

# "already implemented"
#@register.simple_tag
#def user_groupbox(username):
#    pass

@register.inclusion_tag("messaging/tag_followbutton.html")
def tag_followbutton(tagname, requestuser):
    return dict(tagname=tagname,
                alreadyfollowing=bool(Following.objects.filter(follower=get_endpoint_or_none("@"+requestuser), target=get_endpoint_or_none("#"+tagname))))

