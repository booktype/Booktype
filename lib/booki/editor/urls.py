from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'booki.editor.views.view_project', name='view_project'),
    url(r'^edit/', 'booki.editor.views.view_editor', name='view_editor'),  

    # view book 
    url(r'^(?P<edition>[\w\s\_\.\-]+)/edit/$', 'booki.editor.views.edit_book', name='edit_book'),
    url(r'^(?P<edition>[\w\s\_\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.editor.views.view_chapter', name='view_chapter'),
    url(r'^(?P<edition>[\w\s\_\.\-]+)/$', 'booki.editor.views.view_book', name='view_book'),

    url(r'^(?P<edition>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$',  'booki.editor.views.view_attachment', name='view_attachment')
)
