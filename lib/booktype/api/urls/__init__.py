from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from django.conf.urls import url, include

from ..account import views as account_views
from ..editor import views as editor_views


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

    # auth login/logout
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^v1/', include('booktype.api.urls.v1', namespace='v1')),
]
