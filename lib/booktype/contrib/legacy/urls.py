from django.conf.urls import patterns, url, include
from django.views.decorators.csrf import csrf_exempt

from .views import ConvertView, ConvertResourceView


urlpatterns = patterns('',
    url(r'^(?P<resource_id>.+)$', ConvertResourceView.as_view(), name='convert_resource'),
    url(r'^$', csrf_exempt(ConvertView.as_view()), name='convert'),
)