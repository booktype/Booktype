from django.conf.urls.defaults import *


# TODO:
# - portal stuff should go outside!

urlpatterns = patterns('',
    # utils                       
    url(r'^_utils/thumbnail/(?P<attachment>.*)$',  'booki.editor.views.thumbnail_attachment', name='thumbnail_attachment'),

    url(r'^_upload/$',  'booki.editor.views.upload_attachment', name='upload_attachment'),

    url(r'^static/(?P<attachment>.*)$',  'booki.reader.views.attachment', name='view_attachment'),

    url(r'^_full/$', 'booki.reader.views.view_full', name='view_full'),                       

    # view book 
    url(r'^edit/$', 'booki.editor.views.edit_book', name='edit_book'),

    url(r'^(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.view_chapter', name='view_chapter'),

    # json booklist for jquery ui autocomplete
    url(r'^edit/book-list.json$', 'booki.editor.views.view_books_autocomplete'),

    # new stuff for attachments                      
    url(r'^edit/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
    url(r'^(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),


    url(r'^$', 'booki.reader.views.view_book', name='view_book')
)
