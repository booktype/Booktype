import django_filters

from booktype.apps.core.models import Role


class RoleFilter(django_filters.FilterSet):
    """
    FILTERS FOR core.Role MODEL 
    """
    name = django_filters.CharFilter(name='name', lookup_expr='icontains')
    description = django_filters.CharFilter(name='description', lookup_expr='icontains')

    class Meta:
        model = Role
        fields = ('name', 'description')
