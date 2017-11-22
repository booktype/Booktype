from rest_framework import routers

from django.conf.urls import url, include

from ..views import AuthToken
from ..account import views as account_views
from ..editor import views as editor_views
from ..themes import views as themes_views
from ..core import views as core_views

router = routers.DefaultRouter()
router.register(r'users', account_views.UserViewSet)
router.register(r'books', editor_views.BookViewSet)
router.register(r'languages', editor_views.LanguageViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # current users
    url(r'^users/current/$', account_views.CurrentUser.as_view(),
        name="account_current_user_api"),

    # users/books/languages viewsets
    url(r'^', include(router.urls)),

    # chapters list
    url(r'^books/(?P<pk>[0-9]+)/chapters/$', editor_views.ChapterListCreate.as_view(),
        name="editor_chapter_list_create_api"),

    # chapters detail
    url(r'^books/(?P<book_id>[0-9]+)/chapters/(?P<pk>[0-9]+)/$', editor_views.ChapterRetrieveUpdateDestroy.as_view(),
        name="editor_chapter_retrieve_update_destroy_api"),

    # metadata list
    url(r'^books/(?P<pk>[0-9]+)/metadata/$', editor_views.MetadataListCreate.as_view(),
        name="editor_metadata_list_create_api"),

    # metadata detail
    url(r'^books/(?P<book_id>[0-9]+)/metadata/(?P<pk>[0-9]+)/$', editor_views.MetadataRetrieveUpdateDestroy.as_view(),
        name="editor_metadata_retrieve_update_destroy_api"),

    # users list in the book
    url(r'^books/(?P<pk>[0-9]+)/users/$', editor_views.BookUserList.as_view(),
        name="editor_book_user_list_api"),

    # list of roles assigned to the user in specific book
    url(r'^books/(?P<book_id>[0-9]+)/users/(?P<pk>[0-9]+)/roles/$', editor_views.BookUserDetailRoles.as_view(),
        name="editor_book_user_detail_roles_api"),

    # list of permissions assigned to the user in specific book
    url(r'^books/(?P<book_id>[0-9]+)/users/(?P<pk>[0-9]+)/permissions/$',
        editor_views.BookUserDetailPermissions.as_view(),
        name="editor_book_user_detail_permissions_api"),

    # attachment list in the book
    url(r'^books/(?P<pk>[0-9]+)/attachments/$', editor_views.BookAttachmentList.as_view(),
        name="editor_book_attachment_list_api"),

    # roles list
    url(r'^roles/$', core_views.RoleList.as_view(),
        name="core_role_list_api"),

    # themes list
    url(r'^themes/$', themes_views.ThemeList.as_view(),
        name="themes_theme_list_api"),

    # auth retrieve token
    url(r'^auth-token/$', AuthToken.as_view(),
        name="api_retrieve_authtoken")
]
