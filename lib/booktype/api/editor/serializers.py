# -*- coding: utf-8 -*-
import json
import requests

from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils.translation import ugettext_noop

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from rest_framework import serializers
from rest_framework.exceptions import APIException

import sputnik
from booktype.importer import utils as importer_utils
from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booki.utils.log import logBookHistory, logChapterHistory

from booki.editor.models import Book, BookToc, Language, Chapter, BookStatus
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


class ChapterListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ('id', 'title', 'version', 'status', 'revision', 'url_title', 'created', 'modified')
        read_only_fields = ('version', 'status', 'revision', 'url_title', 'created', 'modified')

    def validate(self, attrs):
        attrs['book'] = self.context['view']._book
        attrs['content'] = u'<h1>{}</h1><p><br/></p>'.format(attrs['title'])
        attrs['content_json'] = u'''{
        "entityMap": {},
        "blocks": [
          {
            "key": "bm8jb",
            "text": "",
            "type": "datablock",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
            "data": {}
          },
          {
            "key": "f29sf",
            "text": "Chapter Title",
            "type": "heading1",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
            "data": {
              "attributes": {
                "style": {}
              }
            }
          },
          {
            "key": "a4d8p",
            "text": "",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
            "data": {}
          }
        ]
        }'''
        attrs['url_title'] = booktype_slugify(attrs['title'])
        attrs['version'] = attrs['book'].version
        attrs['status'] = BookStatus.objects.filter(book=attrs['book']).order_by("-weight")[0]

        # validate title/url_title
        if not len(attrs['url_title']):
            raise serializers.ValidationError({'title': 'Title is empty or contains wrong characters.'})

        # validate title/url_title
        chapter_exists = Chapter.objects.filter(
            book=self.context['view']._book, version=attrs['book'].version, url_title=attrs['url_title']
        ).exists()

        if chapter_exists:
            raise serializers.ValidationError({'title': 'Chapter with this title already exists.'})

        return attrs

    def create(self, validated_data):
        chapter = super(ChapterListCreateSerializer, self).create(validated_data)

        # create toc
        book = self.context['view']._book
        book_version = self.context['view']._book.version
        weight = len(book_version.get_toc()) + 1

        for itm in BookToc.objects.filter(version=book_version, book=book).order_by("-weight"):
            itm.weight = weight
            itm.save()
            weight -= 1

        toc_item = BookToc(
            version=book_version, book=book, name=chapter.title, chapter=chapter, weight=1, typeof=1
        )
        toc_item.save()

        # create chapter history
        history = logChapterHistory(
            chapter=chapter,
            content=chapter.content,
            user=self.context['request'].user,
            comment="created via api",
            revision=chapter.revision
        )

        # create book history
        if history:
            logBookHistory(
                book=book,
                version=book_version,
                chapter=chapter,
                chapter_history=history,
                user=self.context['request'].user,
                kind='chapter_create'
            )

        # TODO
        # this is just playground
        # we must create separate tool to push messages through the sputnik channel from API endpoints
        # without having clientID in request

        # message_info
        channel_name = "/chat/{}/".format(book.id)
        clnts = sputnik.smembers("sputnik:channel:{}:channel".format(channel_name))
        message = {
            'channel': channel_name,
            "command": "message_info",
            "from": self.context['request'].user.username,
            "email": self.context['request'].user.email,
            "message_id": "user_new_chapter",
            "message_args": [self.context['request'].user.username, chapter.title]
        }

        for c in clnts:
            if c.strip() != '':
                sputnik.push("ses:%s:messages" % c, json.dumps(message))

        # chapter_create
        channel_name = "/booktype/book/{}/{}/".format(book.id, book_version.get_version())
        clnts = sputnik.smembers("sputnik:channel:{}:channel".format(channel_name))
        message = {
            'channel': channel_name,
            "command": "chapter_create",
            "chapter": (chapter.id, chapter.title, chapter.url_title, 1, chapter.status.id,
                        chapter.lock_type, chapter.lock_username, "root", toc_item.id, "normal", None)
        }

        for c in clnts:
            if c.strip() != '':
                sputnik.push("ses:%s:messages" % c, json.dumps(message))

        # notificatoin message
        message = {
            'channel': channel_name,
            'command': 'notification',
            'message': 'notification_chapter_was_created',
            'username': self.context['request'].user.username,
            'message_args': (chapter.title,)
        }

        for c in clnts:
            if c.strip() != '':
                sputnik.push("ses:%s:messages" % c, json.dumps(message))

        return chapter


class ChapterRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = '__all__'
        read_only_fields = ('version', 'book', 'revision', 'url_title', 'created', 'modified')

    def validate_status(self, status):
        if self.context['view']._book.id is not status.book.id:
            raise serializers.ValidationError('Wrong status id. Options are {}'.format(
                [i['id'] for i in BookStatus.objects.filter(book=self.context['view']._book).values('id')]
            ))

        return status

    def validate_content_json(self, content_json):
        try:
            json.loads(content_json)
        except ValueError as e:
            raise serializers.ValidationError("Not valid json: {}".format(e))

        return content_json
