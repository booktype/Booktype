# -*- coding: utf-8 -*-
import requests
from django.core.files.base import ContentFile

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from django.utils.translation import ugettext_noop

from rest_framework import serializers
from rest_framework.exceptions import APIException

from booktype.importer import utils as importer_utils
from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier

from booki.editor.models import Book, BookToc, Language
from booktype.utils.book import create_book
from booktype.apps.core.models import BookRole
from booktype.utils.misc import booktype_slugify

from ..account.serializers import SimpleUserSerializer


class LanguageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'abbrevation', 'name', 'url']


class BookListSerializer(serializers.ModelSerializer):
    editor_url = serializers.SerializerMethodField(read_only=True)

    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        read_only=True
    )
    language = LanguageSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'owner', 'title', 'url', 'description',
            'created', 'editor_url', 'language'
        ]
        read_only_fields = ['id', 'url', 'created']

    def get_editor_url(self, obj):
        request = self.context['request']
        url = reverse('edit:editor', args=[obj.url_title])
        return request.build_absolute_uri(url)


class BookSerializer(BookListSerializer):
    toc = serializers.SerializerMethodField(read_only=True)
    metadata = serializers.SerializerMethodField(read_only=True)
    language_id = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(),
        source='language')

    users_by_role = serializers.HyperlinkedIdentityField(
        view_name='book-users-by-role')

    class Meta(BookListSerializer.Meta):
        parent = BookListSerializer.Meta
        fields = parent.fields + ['toc', 'metadata', 'language_id', 'users_by_role']
        depth = 1

    def get_toc(self, obj):
        book_url = self.get_editor_url(obj)

        def _build_toc_entry(item):
            if item.is_chapter():
                return {
                    'title': item.chapter.title,
                    'url_title': item.chapter.url_title,
                    'typeof': item.typeof,
                    'typeof_label': ugettext_noop('Chapter'),
                    'editor_url': '{0}#edit/{1}'.format(book_url, item.chapter.id),
                    'current_editor': item.chapter.get_current_editor_username()
                }
            else:
                entry = {
                    'name': item.name,
                    'editor_url': None,
                    'children': [],
                    'typeof': item.typeof,
                    'typeof_label': ugettext_noop('Section')
                }

                if item.has_children():
                    entry['children'] = map(_build_toc_entry, item.children())

                return entry

        version = obj.get_version()
        items = BookToc.objects.filter(version=version, parent__isnull=True).order_by("-weight")
        return map(_build_toc_entry, items)

    def get_metadata(self, obj):
        return [{'name': x.name, 'value': x.get_value()} for x in obj.metadata]


class BookCreateSerializer(BookSerializer):

    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='owner')
    import_book_url = serializers.URLField(write_only=True, required=False)
    import_book_format = serializers.ChoiceField(
        choices=['epub', 'docx'], write_only=True, required=False)

    class Meta(BookSerializer.Meta):
        parent = BookSerializer.Meta
        fields = parent.fields + [
            'owner_id', 'import_book_url', 'import_book_format']

    def validate(self, data):
        data = super(BookCreateSerializer, self).validate(data)

        fields = data.keys()
        if 'import_book_url' in fields and 'import_book_format' not in fields:
            raise serializers.ValidationError({'import_book_format': ["This field is required."]})

        return data

    def create(self, validated_data):
        n = Book.objects.count()
        book_title = validated_data['title']
        owner = validated_data['owner']
        url_title = '%s-%s' % (n, booktype_slugify(book_title))

        book = create_book(owner, book_title, book_url=url_title)
        book.language = validated_data.get('language', None)
        book.save()

        import_book_url = validated_data.get('import_book_url')
        import_format = validated_data.get('import_book_format')

        if import_book_url:
            book_file = self._get_book_file(import_book_url)
            try:
                book_importer = importer_utils.get_importer_module(import_format)
            except Exception as err:
                raise serializers.ValidationError("Wrong importer format {}".format(err))

            delegate = Delegate()
            notifier = CollectNotifier()

            try:
                book_importer(book_file, book, notifier=notifier, delegate=delegate)
            except Exception as err:
                raise APIException("Unexpected error while importing the file {}".format(err))

            if len(notifier.errors) > 0:
                err = "\n".join(notifier.errors)
                raise APIException("Something went wrong: {}".format(err))

        return book

    def _get_book_file(self, url):
        try:
            response = requests.get(url)
            book_file = ContentFile(response.content)
        except Exception as err:
            raise serializers.ValidationError("Error while retrieving the file {}".format(err))

        return book_file


class BookRoleSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(source='role.name', read_only=True)
    members = SimpleUserSerializer(many=True)

    class Meta:
        model = BookRole
        fields = ['id', 'name', 'members']
        depth = 1
