# -*- coding: utf-8 -*-
from rest_framework import serializers

from booktype.apps.core.models import Role, BookRole

from ..account.serializers import SimpleUserSerializer

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class RoleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions')
        depth = 1


class BookRoleSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(source='role.name', read_only=True)
    members = SimpleUserSerializer(many=True)

    class Meta:
        model = BookRole
        fields = ['id', 'name', 'members']
        depth = 1


class SimpleRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions')
        depth = 2


class SimpleBookRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRole
        fields = ('id', 'role')
        depth = 2
