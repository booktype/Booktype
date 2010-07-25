from django.conf.urls.defaults import *


# TODO:
# - portal stuff should go outside!

urlpatterns = patterns('',
    # utils                       
    url(r'^_utils/thumbnail/(?P<attachment>.*)$',  'booki.editor.views.thumbnail_attachment', name='thumbnail_attachment'),

    url(r'^_upload/$',  'booki.editor.views.upload_attachment', name='upload_attachment'),


#    url(r'^(?P<edition>[\w\s\_\.\-]+)/export/{0,1}$',  'booki.editor.views.view_export', name='export_booki'), # modify this one
    url(r'^static/(?P<attachment>.*)$',  'booki.reader.views.view_attachment', name='view_attachment'),


    url(r'^_full/$', 'booki.reader.views.view_full', name='view_full'),                       

    # view book 
    url(r'^edit/$', 'booki.editor.views.edit_book', name='edit_book'),

    url(r'^(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.view_chapter', name='view_chapter'),
    url(r'^$', 'booki.reader.views.view_book', name='view_book')
)
