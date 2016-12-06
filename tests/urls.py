from django.conf.urls import url, include

import booktype.urls

from django.contrib import admin
admin.autodiscover()

# Register additional URls
urlpatterns = [
    # Django Admin interface is disabled by default. If you want it
    # enabled you will have to uncomment couple of lines here.
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
] + booktype.urls.urlpatterns
