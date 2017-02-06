from django.contrib.auth.models import User
from rest_framework import serializers


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
