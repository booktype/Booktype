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
    url(r'^_edit/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
    url(r'^_edit/book-list.json$', 'booki.editor.views.view_books_autocomplete'),

    # draft of a book
#_v/(?P<version>[\w\s\_\d\.\-]+)/
    #url(r'^_draft/static/(?P<attachment>.*)$',  'booki.reader.views.attachment', name='view_attachment'),

    url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.draft_chapter', name='draft_chapter'),
    url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
    url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment', name='draft_attachment'),
    url(r'^_draft/_v/(?P<version>[\w\s\_\d\.\-]+)/$', 'booki.reader.views.draft_book', name='draft_book'),

    url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.draft_chapter', name='draft_chapter'),
    url(r'^_draft/(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
    url(r'^_draft/$', 'booki.reader.views.draft_book', name='draft_book'),


    url(r'^_info/$', 'booki.reader.views.book_info', name='book_info'),
    url(r'^_info/cover.jpg$', 'booki.reader.views.book_cover', name='book_cover'),
    url(r'^_info/edit/$', 'booki.reader.views.edit_info', name='edit_info'),

    # this should be                       
    url(r'^(?P<chapter>[\w\s\_\.\-]+)/$', 'booki.reader.views.book_chapter', name='book_chapter'),
    url(r'^(?P<chapter>[\w\s\_\.\-]+)/static/(?P<attachment>.*)$', 'booki.reader.views.staticattachment'),
    url(r'^$', 'booki.reader.views.book_view', name='book_view')
)
