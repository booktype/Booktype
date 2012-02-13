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


from django.utils.translation import ugettext_lazy as _

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail

from django.http import HttpResponse

from booki.messaging.models import Post, PostAppearance, Endpoint, Following
from django.contrib.auth import models as auth_models

from booki.editor.models import BookiGroup, Book

from django.core.exceptions import ObjectDoesNotExist

def get_or_none(objects, *args, **kwargs):
    try:
        return objects.get(*args, **kwargs)
    except ObjectDoesNotExist:
        return None

def get_endpoint_or_none(syntax):
    timeline = get_or_none(Endpoint.objects, syntax=syntax)

    if not timeline:
        if syntax.startswith('@'):
            # check that the user exists before creating the endpoint
            user = get_or_none(auth_models.User.objects, username=syntax[1:])
            if user:
                timeline = Endpoint(syntax=syntax)
                timeline.save()
        if syntax.startswith('!'):
            group = get_or_none(BookiGroup.objects, url_name=syntax[1:])
            if group:
                timeline = Endpoint(syntax=syntax)
                timeline.save()
        if syntax.startswith(u'\u212c'):
            book = get_or_none(Book.objects, url_title=syntax[1:])
            if book:
                timeline = Endpoint(syntax=syntax)
                timeline.save()
        if syntax.startswith('#'):
            timeline = Endpoint(syntax=syntax)
            timeline.save()

    return timeline

def user2endpoint(user):
    return get_endpoint_or_none("@"+user.username)

def push_notification(request, message, timeline):
    import sputnik

    sputnik.addMessageToChannel(request, "/messaging/%s/" % timeline, {"command": "message_received", "message": message})


def add_appearance_for_user(message, word, sent, direct=False, orig_word=None):
    timeline = get_endpoint_or_none(word)
    if timeline and timeline not in sent:
        appearance = PostAppearance(
            post=message, timestamp=message.timestamp, 
            endpoint=timeline)
        appearance.save()
        sent[timeline] = True

        if timeline.wants_notification(message, orig_word):
            # XXX wanted has to be first to be sent to take effect
            # XXX check that email addr is verified before sending

            user = timeline.as_user()
            SERVER_ROOT = "/".join(settings.BOOKI_URL.split("/")[:3])
            body = render_to_string('messaging/new_message_email.txt', 
                                    dict(user=user, post=message,
                                         SERVER_ROOT=SERVER_ROOT,
                                         DATA_URL=settings.DATA_URL))
            if orig_word == word or not orig_word:
                reason = message.sender
            else:
                reason = orig_word
            send_mail(_('Message from %s at Booki') % reason, 
                      body,
                      settings.EMAIL_HOST_USER,
                      [user.email], fail_silently=False)

def add_appearance_for_followers(message, word, sent, direct=False, orig_word=None):
    source_endpoint = get_endpoint_or_none(word)
    followings = Following.objects.filter(target=source_endpoint)
    for following in followings:
        target = following.follower.syntax
        add_appearance_for_user(message, target, sent, direct, orig_word)

def add_appearance_for_group(message, word, sent, direct=False, orig_word=None):
    timeline = get_endpoint_or_none(word)
    if timeline and timeline not in sent:
        appearance = PostAppearance(
            post=message, timestamp=message.timestamp, 
            endpoint=timeline)
        appearance.save()
        sent[timeline] = True

        # members "follow" their groups
        group = get_or_none(BookiGroup.objects, url_name=word[1:])
        for user in group.members.all():
            add_appearance_for_user(message, "@"+user.username, sent, direct, orig_word)

def add_appearance_for_book(message, word, sent, direct=False, orig_word=None):
    timeline = get_endpoint_or_none(word)
    if timeline and timeline not in sent:
        appearance = PostAppearance(
            post=message, timestamp=message.timestamp, 
            endpoint=timeline)
        appearance.save()
        sent[timeline] = True

        # followers of the book tag
        add_appearance_for_followers(message, word, sent, False, orig_word)

        # group "follows" its books
        book = get_or_none(Book.objects, url_title=word[1:])
        if book and book.group:
            add_appearance_for_group(message, "!"+book.group.url_name, sent, direct, orig_word)

def add_appearance_for_tag(message, word, sent, direct=False, orig_word=None):
    timeline = get_endpoint_or_none(syntax=word)
    if timeline and timeline not in sent:
        appearance = PostAppearance(
            post=message, timestamp=message.timestamp, 
            endpoint=timeline)
        appearance.save()
        sent[timeline] = True

        # followers of the tag
        add_appearance_for_followers(message, word, sent, False, orig_word)


@login_required
def view_post(request):
    # XXX validate:
    content = request.POST.get('content')
    attachment = request.FILES.get('attachment')
    context_url = request.POST.get('context_url')
    snippet = request.POST.get('snippet')
    ajax = request.POST.get('ajax')

    message = Post(sender=user2endpoint(request.user), content=content, 
                   attachment=attachment, context_url=context_url,
                   snippet=snippet)
    message.save()

    # add appearances:

    sent = dict()

    # mentions
    for word in content.split():
        if word.startswith("@"):
            add_appearance_for_user(message, word, sent, True, word)
        if word.startswith("!"):
            add_appearance_for_group(message, word, sent, True, word)
        if word.startswith(u"\u212c"):
            add_appearance_for_book(message, word, sent, True, word)
        if word.startswith("#"):
            add_appearance_for_tag(message, word, sent, True, word)

    # followers of the sending user
    add_appearance_for_followers(message, "@"+request.user.username, sent, False, None)

    # FIXME
    request.clientID = "999"
    request.sputnikID = "999"

    html_message = render_to_string("messaging/post.html", dict(post=message))
    for timeline in sent:
        push_notification(request, html_message, timeline)
    # ensure the timeline of the sender is notified
    if user2endpoint(request.user) not in sent:
        push_notification(request, html_message, user2endpoint(request.user))

    if not ajax:
        return redirect('view_profile', request.user.username)
    else:
        return HttpResponse("Sent.", mimetype="text/plain")

@login_required
def view_follow(request):
    target_syntax = request.POST.get('target')
    # FIXME may fail
    target = get_endpoint_or_none(target_syntax)

    follower = user2endpoint(request.user)

    if (not Following.objects.filter(follower=follower, target=target)
        and not target==follower):
        following = Following(follower=follower, target=target)
        following.save()

    return redirect('view_profile', request.user.username)

@login_required
def view_unfollow(request):
    target_syntax = request.POST.get('target')
    # FIXME may fail
    target = get_endpoint_or_none(target_syntax)

    follower = user2endpoint(request.user)

    Following.objects.filter(follower=follower, target=target).delete()

    return redirect('view_profile', request.user.username)


def view_tag(request, tagname):
    tag = get_object_or_404(Endpoint, syntax="#"+tagname)

    return render_to_response("messaging/view_tag.html",
                              dict(tag=tag,
                                   tagname=tagname,
                                   request=request))
