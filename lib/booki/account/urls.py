from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'booki.account.views.view_accounts', name='view_accounts'),

    url(r'^signin/$', 'booki.account.views.signin', name='signin'),  
    url(r'^login/$', 'booki.account.views.signin', name='login'),  
    url(r'^forgot_password/$', 'booki.account.views.forgotpassword', name='forgotpassword'),  
    url(r'^forgot_password/enter/$', 'booki.account.views.forgotpasswordenter', name='forgotpasswordenter'),  

    url(r'^signout/$', 'booki.account.views.signout', name='signout'),  

#    url(r'^register/$', 'booki.account.views.register', name='register'),

    # Username
    # Letters, digits and @/./+/-/_ only.
    # For now, even space.                       

    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/$', 'booki.account.views.view_profile', name='view_profile'),
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/settings/$', 'booki.account.views.user_settings', name='user_settings'),                     
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/my_books/$', 'booki.account.views.my_books', name='my_books'),                     
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/my_groups/$', 'booki.account.views.my_groups', name='my_groups'),                     
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/my_people/$', 'booki.account.views.my_people', name='my_people'),
    url(r'^(?P<username>[\w\d\@\.\+\-\_\s]+)/create_book/$', 'booki.account.views.create_book', name='create_book')
)
