import django_filters

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
