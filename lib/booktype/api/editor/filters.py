import django_filters

from django.contrib.auth.models import User

from booki.editor.models import Chapter


class ChapterFilter(django_filters.FilterSet):
    """
    FILTERS FOR editor.Chapter MODEL 
    """
    version = django_filters.NumberFilter(name='version', lookup_expr='exact')
    book = django_filters.NumberFilter(name='book', lookup_expr='exact')
    url_title = django_filters.CharFilter(name='url_title', lookup_expr='icontains')
    title = django_filters.CharFilter(name='title', lookup_expr='icontains')
    status = django_filters.NumberFilter(name='status', lookup_expr='exact')
    to_created = django_filters.DateTimeFilter(name='created', lookup_expr='lte')
    from_created = django_filters.DateTimeFilter(name='created', lookup_expr='gte')
    to_modified = django_filters.DateTimeFilter(name='modified', lookup_expr='lte')
    from_modified = django_filters.DateTimeFilter(name='modified', lookup_expr='gte')
    max_revision = django_filters.NumberFilter(name='revision', lookup_expr='lte')
    min_revision = django_filters.NumberFilter(name='revision', lookup_expr='gte')
    content = django_filters.CharFilter(name='content', lookup_expr='icontains')
    content_json = django_filters.CharFilter(name='content_json', lookup_expr='icontains')

    class Meta:
        model = Chapter
        fields = ('version', 'book', 'url_title', 'title', 'status', 'to_created', 'from_created', 'to_modified',
                  'from_modified', 'max_revision', 'min_revision', 'content', 'content_json')


class BookUserListFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(name='username', lookup_expr='icontains')
    first_name = django_filters.CharFilter(name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(name='last_name', lookup_expr='icontains')
    email = django_filters.CharFilter(name='email', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
