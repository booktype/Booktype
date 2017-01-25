from django.conf.urls import url, include
from rest_framework import routers

from .views import AuthToken
from .account import views as account_views
from .editor import views as editor_views

from rest_framework_swagger.views import get_swagger_view
schema_view = get_swagger_view(title='Booktype API')

router = routers.DefaultRouter()
router.register(r'users', account_views.UserViewSet)
router.register(r'books', editor_views.BookViewSet)
router.register(r'languages', editor_views.LanguageViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^$', schema_view),
    url(r'^', include(router.urls)),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^auth-token/', AuthToken.as_view())
]
