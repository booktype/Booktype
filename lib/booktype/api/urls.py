from django.conf.urls import url, include
from rest_framework import routers

from .views import AuthToken
from .account import views as account_views
from .editor import views as editor_views
from .core import views as core_views

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Booktype API')

router = routers.DefaultRouter()
router.register(r'users', account_views.UserViewSet)
router.register(r'books', editor_views.BookViewSet)
router.register(r'languages', editor_views.LanguageViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # swagger
    url(r'^$', schema_view),

    # users
    url(r'^users/current/$', account_views.CurrentUser.as_view(), name="account_current_user_api"),

    # users/books/languages viewsets
    url(r'^', include(router.urls)),

    # chapters
    url(r'^books/(?P<pk>[0-9]+)/chapters/$',
        editor_views.ChapterListCreate.as_view(),
        name="editor_chapter_list_create_api"),

    url(r'^books/(?P<book_id>[0-9]+)/chapters/(?P<pk>[0-9]+)/$',
        editor_views.ChapterRetrieveUpdateDestroy.as_view(),
        name="editor_chapter_retrive_update_destroy_api"),

    # users in the book
    url(r'^books/(?P<pk>[0-9]+)/users/$',
        editor_views.BookUserList.as_view(),
        name="editor_book_user_list_api"),

    url(r'^books/(?P<book_id>[0-9]+)/users/(?P<pk>[0-9]+)/roles/$',
        editor_views.BookUserDetailRoles.as_view(),
        name="editor_book_user_detail_roles_api"),

    url(r'^books/(?P<book_id>[0-9]+)/users/(?P<pk>[0-9]+)/permissions/$',
        editor_views.BookUserDetailPermissions.as_view(),
        name="editor_book_user_detail_permissions_api"),

    # roles
    url(r'^roles/$',
        core_views.RoleList.as_view(),
        name="core_role_list_api"),

    # auth login/logout
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    # auth retrieve token
    url(r'^auth-token/$', AuthToken.as_view(),
        name="api_retrieve_authtoken")
]
