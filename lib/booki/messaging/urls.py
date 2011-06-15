from django.conf.urls.defaults import *

urlpatterns = patterns('booki.messaging.views',
    (r'^post$', 'view_post'),
    (r'^follow$', 'view_follow'),
    (r'^unfollow$', 'view_unfollow'),
    (r'^tags/([\w]+)$', 'view_tag', None, 'view_tag'),
)
