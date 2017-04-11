import django_filters

from django.contrib.auth.models import User


class UserFilter(django_filters.FilterSet):
    """
    FILTERS FOR auth.User MODEL 
    """
    to_last_login = django_filters.DateTimeFilter(name='last_login', lookup_expr='lte')
    from_last_login = django_filters.DateTimeFilter(name='last_login', lookup_expr='gte')
    is_superuser = django_filters.BooleanFilter(name='is_superuser', lookup_expr='exact')
    username = django_filters.CharFilter(name='username', lookup_expr='icontains')
    first_name = django_filters.CharFilter(name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(name='last_name', lookup_expr='icontains')
    email = django_filters.CharFilter(name='email', lookup_expr='icontains')
    is_staff = django_filters.BooleanFilter(name='is_staff', lookup_expr='exact')
    is_active = django_filters.BooleanFilter(name='is_active', lookup_expr='exact')
    to_date_joined = django_filters.DateTimeFilter(name='date_joined', lookup_expr='lte')
    from_date_joined = django_filters.DateTimeFilter(name='date_joined', lookup_expr='gte')

    class Meta:
        model = User
        fields = (
        'to_last_login', 'from_last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff',
        'is_active', 'to_date_joined', 'from_date_joined')
