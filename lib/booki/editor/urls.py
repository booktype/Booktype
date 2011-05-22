from django.conf.urls.defaults import *


# TODO:
# - portal stuff should go outside!
# - what a mess this is! must clean it. must clean it.

urlpatterns = patterns('',
    # utils                       
    url(r'^_utils/thumbnail/(?P<attachment>.*)$',  'booki.editor.views.thumbnail_attachment', name='thumbnail_attachment'),

    url(r'^_upload/$',  'booki.editor.views.upload_attachment', name='upload_attachment'),

    url(r'^_full/$', 'booki.reader.views.view_full', name='view_full'),                       

    # edit book 
    url(r'^_edit/$', 'booki.editor.views.edit_book', name='edit_book'),

    # change this                       
    url(r'^_draft/static/(?P<attachment>.*)$',  'booki.reader.views.attachment', name='view_attachment'),
    url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.view_chapter', name='view_chapter'),
    url(r'^_draft/$', 'booki.reader.views.view_draft', name='view_draft'),

    # json booklist for jquery ui autocomplete
    url(r'^_edit/book-list.json$', 'booki.editor.views.view_books_autocomplete'),

    # new stuff for attachments                      
    url(r'^_edit/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
    url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),


    url(r'^$', 'booki.reader.views.view_book', name='view_book')
)
