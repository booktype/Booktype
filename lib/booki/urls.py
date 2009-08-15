from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # front page                       
    url(r'^$', 'booki.editor.views.view_frontpage'),

    # this is temp
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_DOC_ROOT}),

    # user accounts                     
    url(r'^accounts/', include('booki.account.urls')),                    

    # the rest interface                   
    url(r'^api/$', 'booki.editor.views.dispatcher'),                     

    # reader
    url(r'^(?P<project>[\w\s\_\.\-]+)/', include('booki.editor.urls')),
)
