from django.contrib.auth.models import User
from rest_framework import serializers

from booktype.apps.account import utils as account_utils

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'url', 'username', 'email',
            'first_name', 'last_name', 'is_active',
            'last_login', 'is_superuser'
        )
        read_only_fields = ['id', 'last_login', 'is_superuser']


class SimpleUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ['id', 'url']
        read_only_fields = ['id', 'url']


class DetailedUserSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_active',
            'last_login', 'is_superuser', 'profile_url',
            'profile_image_url', 'get_full_name'
        )

    def get_profile_image_url(self, obj):
        return account_utils.get_profile_image(obj)

    def get_profile_url(self, obj):
        return reverse('accounts:view_profile', args=[obj.username])
