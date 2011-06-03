
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

@register.simple_tag
def book_timeline(bookname):
    pass

@register.inclusion_tag("messaging/timeline.html")
def tag_timeline(tagname):
    endpoint = get_endpoint_or_none("#"+tagname)
    appearances = PostAppearance.objects.filter(endpoint=endpoint)
    tag_posts = (x.post for x in appearances.order_by("-timestamp"))
    return dict(syntax="#"+tagname, posts=tag_posts)

### messagefields:

@register.simple_tag
def user_messagefield(username):
    pass

@register.simple_tag
def group_messagefield(groupname):
    pass

@register.simple_tag
def book_messagefield(bookname):
    pass

def messagefield():
    pass

@register.simple_tag
def messagefield_button():
    pass

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
    return dict(tags=tags)

@register.inclusion_tag("messaging/user_followbutton.html")
def user_followbutton(username):
    return dict(username=username)

@register.simple_tag
def book_followbutton(bookname):
    pass

# "already implemented"
#@register.simple_tag
#def user_groupbox(username):
#    pass

@register.inclusion_tag("messaging/tag_followbutton.html")
def tag_followbutton(tagname):
    return dict(tagname=tagname)

