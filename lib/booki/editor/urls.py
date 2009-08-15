from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'booki.editor.views.view_project', name='view_project'),
    url(r'^edit/', 'booki.editor.views.view_editor', name='view_editor'),  

    # i wonder what is this and why i put it here 
    url(r'^attachment/(?P<attachment>\w+)/$', 'booki.editor.views.view_attachment', name='view_attachment'),

    # view book edition
    url(r'^(?P<edition>[\w\s\_\.\-]+)/edit/$', 'booki.editor.views.edit_book', name='edit_edition'),
    url(r'^(?P<edition>[\w\s\_\.\-]+)/$', 'booki.editor.views.view_book', name='view_edition')
)
