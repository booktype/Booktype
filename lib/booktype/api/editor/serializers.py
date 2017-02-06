try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_noop

from rest_framework import serializers

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

    class Meta(BookSerializer.Meta):
        parent = BookSerializer.Meta
        fields = parent.fields + ['owner_id']

    def create(self, validated_data):
        n = Book.objects.count()
        book_title = validated_data['title']
        owner = validated_data['owner']
        url_title = '%s-%s' % (n, booktype_slugify(book_title))

        book = create_book(owner, book_title, book_url=url_title)
        book.language = validated_data.get('language', None)
        book.save()

        return book


class BookRoleSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(source='role.name', read_only=True)
    members = SimpleUserSerializer(many=True)

    class Meta:
        model = BookRole
        fields = ['id', 'name', 'members']
        depth = 1
