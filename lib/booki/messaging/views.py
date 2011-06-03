
from django.utils.translation import ugettext_lazy as _

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail

from booki.messaging.models import Post, PostAppearance, Endpoint, Following
from django.contrib.auth import models as auth_models

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
        if syntax.startswith('#'):
            timeline = Endpoint(syntax=syntax)
            timeline.save()

    return timeline

def user2endpoint(user):
    return get_endpoint_or_none("@"+user.username)

@login_required
def view_post(request):
    content = request.POST.get('content')
    attachment = request.FILES.get('attachment')

    message = Post(sender=user2endpoint(request.user), content=content, 
                   attachment=attachment)
    message.save()

    # add appearances:

    sent = dict()

    # mentions
    for word in content.split():
        if word.startswith("@"):
            timeline = get_endpoint_or_none(word)
            if timeline and timeline not in sent:
                appearance = PostAppearance(
                    post=message, timestamp=message.timestamp, 
                    endpoint=timeline)
                appearance.save()
                sent[timeline] = True

                # XXX check that email addr is verified before sending
                user = timeline.as_user()
                SERVER_ROOT = "/".join(settings.BOOKI_URL.split("/")[:3])
                body = render_to_string('messaging/new_message_email.txt', 
                                        dict(user=user, post=message,
                                             SERVER_ROOT=SERVER_ROOT,
                                             DATA_URL=settings.DATA_URL))
                send_mail(_('Direct message from %s at Booki') % message.sender, 
                          body,
                          'tuukka@labs.seravo.fi',
                          [user.email], fail_silently=False)

        if word.startswith("!"):
            timeline = get_endpoint_or_none(word)
            if timeline and timeline not in sent:
                appearance = PostAppearance(
                    post=message, timestamp=message.timestamp, 
                    endpoint=timeline)
                appearance.save()
                sent[timeline] = True
        if word.startswith("#"):
            timeline = get_endpoint_or_none(syntax=word)
            if timeline and timeline not in sent:
                appearance = PostAppearance(
                    post=message, timestamp=message.timestamp, 
                    endpoint=timeline)
                appearance.save()
                sent[timeline] = True

    # followers
    source_endpoint = user2endpoint(request.user)
    followings = Following.objects.filter(target=source_endpoint)
    for following in followings:
        target = following.follower.syntax
        timeline = get_endpoint_or_none(syntax=target)
        if timeline and timeline not in sent:
            appearance = PostAppearance(
                post=message, timestamp=message.timestamp, 
                endpoint=timeline)
            appearance.save()
            sent[timeline] = True

    return redirect('view_profile', request.user.username)

@login_required
def view_follow(request):
    target_syntax = request.POST.get('target')
    # FIXME may fail
    target = get_endpoint_or_none(target_syntax)

    follower = user2endpoint(request.user)

    if not Following.objects.filter(follower=follower, target=target):
        following = Following(follower=follower, target=target)
        following.save()

    return redirect('view_profile', request.user.username)

# XXX    return 

def view_tag(request, tagname):
    tag = get_object_or_404(Endpoint, syntax="#"+tagname)

    return render_to_response("messaging/view_tag.html",
                              dict(tag=tag,
                                   tagname=tagname))
