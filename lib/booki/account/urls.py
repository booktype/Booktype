from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'booki.account.views.view_accounts', name='view_accounts'),

    url(r'^signin/$', 'booki.account.views.signin', name='signin'),  
    url(r'^login/$', 'booki.account.views.signin', name='login'),  

    url(r'^signout/$', 'booki.account.views.signout', name='signout'),  

    url(r'^register/$', 'booki.account.views.register', name='register'),


    url(r'^(?P<username>\w+)/$', 'booki.account.views.view_profile', name='view_profile'),
    url(r'^(?P<username>\w+)/settings/$', 'booki.account.views.user_settings', name='user_settings'),                     
    url(r'^(?P<username>\w+)/my_books/$', 'booki.account.views.my_books', name='my_books'),                     
    url(r'^(?P<username>\w+)/my_groups/$', 'booki.account.views.my_groups', name='my_groups'),                     
    url(r'^(?P<username>\w+)/my_people/$', 'booki.account.views.my_people', name='my_people')                     
)
