# -*- coding: utf-8 -*-
import os
import json
import requests
import logging

from rest_framework import serializers
from rest_framework.exceptions import APIException

from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils.translation import ugettext_noop
from django.conf import settings

import sputnik
from booktype.importer import utils as importer_utils
from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booktype.apps.account import utils as account_utils
from booktype.apps.edit.forms import AdditionalMetadataForm
from booktype.utils.book import create_book
from booktype.utils.misc import booktype_slugify
from booki.utils.log import logBookHistory, logChapterHistory
from booki.editor.models import (Book, BookToc, Language, Chapter, BookStatus,
                                 Info, METADATA_FIELDS, Attachment,
                                 get_attachment_url)

from ..core.serializers import SimpleBookRoleSerializer

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

try:
    from PIL import Image
except ImportError:
    import Image


logger = logging.getLogger('api.editor.serializers')


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
            error = {'import_book_format': ["This field is required."]}
            logger.warn('BookCreateSerializer validate: {}'.format(error))
            raise serializers.ValidationError(error)

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
                error = "Wrong importer format {}".format(err)
                logger.warn('BookCreateSerializer create: {}'.format(error))
                raise serializers.ValidationError(error)

            delegate = Delegate()
            notifier = CollectNotifier()

            try:
                book_importer(book_file, book, notifier=notifier, delegate=delegate)
            except Exception as err:
                error_msg = "Unexpected error while importing the file {}".format(err)
                logger.warn('BookCreateSerializer create: {}'.format(error_msg))
                raise APIException(error_msg)

            if len(notifier.errors) > 0:
                err = "\n".join(notifier.errors)
                error_msg = "Something went wrong: {}".format(err)
                logger.warn('BookCreateSerializer create: {}'.format(error_msg))
                raise APIException(error_msg)

        return book

    def _get_book_file(self, url):
        try:
            response = requests.get(url)
            book_file = ContentFile(response.content)
        except Exception as err:
            error_msg = "Error while retrieving the file {}".format(err)
            logger.warn('BookCreateSerializer create: {}'.format(error_msg))
            raise serializers.ValidationError(error_msg)

        return book_file


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
            error_msg = {'title': 'Title is empty or contains wrong characters.'}
            logger.warn('ChapterListCreateSerializer validate: {}'.format(error_msg))
            raise serializers.ValidationError(error_msg)

        # validate title/url_title
        chapter_exists = Chapter.objects.filter(
            book=self.context['view']._book, version=attrs['book'].version, url_title=attrs['url_title']
        ).exists()

        if chapter_exists:
            error_msg = {'title': 'Chapter with this title already exists.'}
            logger.warn('ChapterListCreateSerializer validate: {}'.format(error_msg))
            raise serializers.ValidationError(error_msg)

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
            error_msg = 'Wrong status id. Options are {}'.format(
                [i['id'] for i in BookStatus.objects.filter(book=self.context['view']._book).values('id')]
            )
            logger.warn('ChapterRetrieveUpdateDestroySerializer validate_status: {}'.format(error_msg))
            raise serializers.ValidationError(error_msg)

        return status

    def validate_content_json(self, content_json):
        try:
            json.loads(content_json)
        except ValueError as e:
            error_msg = "Not valid json: {}".format(e)
            logger.warn('ChapterRetrieveUpdateDestroySerializer validate_content_json: {}'.format(error_msg))
            raise serializers.ValidationError(error_msg)

        return content_json


class MetadataListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Info
        fields = ('id', 'name', 'value_string')

    def validate_name(self, name):
        metadata_keys = set()

        # metadata keys
        for field, _, standard in METADATA_FIELDS:
            metadata_keys.add('%s.%s' % (standard, field))

        # additional metadata keys
        for field, attrs in getattr(settings, 'ADDITIONAL_METADATA', {}).items():
            metadata_keys.add('%s.%s' % (AdditionalMetadataForm.META_PREFIX, field))

        if name not in metadata_keys:
            raise serializers.ValidationError('Wrong metadata name. Options are: {}'.format(
                ', '.join(metadata_keys)
            ))

        book = self.context['view']._book

        if book.info_set.filter(name__exact=name).exists():
            raise serializers.ValidationError('{} already exist. You can update or delete this metadata entry'.format(
                name
            ))

        return name

    def validate(self, attrs):
        _string = 0
        attrs['kind'] = _string
        attrs['book'] = self.context['view']._book

        return attrs


class MetadataRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = Info
        fields = ('id', 'name', 'value_string')

    def validate_name(self, name):
        metadata_keys = set()

        # metadata keys
        for field, _, standard in METADATA_FIELDS:
            metadata_keys.add('%s.%s' % (standard, field))

        # additional metadata keys
        for field, attrs in getattr(settings, 'ADDITIONAL_METADATA', {}).items():
            metadata_keys.add('%s.%s' % (AdditionalMetadataForm.META_PREFIX, field))

        if name not in metadata_keys:
            raise serializers.ValidationError('Wrong metadata name. Options are: {}'.format(
                ', '.join(metadata_keys)
            ))

        book = self.context['view']._book

        if book.info_set.filter(name__exact=name).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError('{} already exist. You can update or delete this metadata entry'.format(
                name
            ))

        return name

    def validate(self, attrs):
        _string = 0
        attrs['kind'] = _string
        attrs['book'] = self.context['view']._book

        return attrs



class BookUserListSerializer(serializers.ModelSerializer):
    book_roles = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'url', 'username', 'email', 'first_name', 'last_name', 'profile_url',
            'profile_image_url', 'get_full_name', 'book_roles'
        )

    def get_book_roles(self, obj):
        book_roles = []
        for role in obj.roles.filter(book=self.context['view']._book):
            book_roles.append(SimpleBookRoleSerializer(role).data)

        return book_roles

    def get_profile_image_url(self, obj):
        return account_utils.get_profile_image(obj)

    def get_profile_url(self, obj):
        return reverse('accounts:view_profile', args=[obj.username])


class BookAttachmentListSerializer(serializers.ModelSerializer):
    attachment = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    dimension = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            'id', 'attachment', 'created', 'version', 'status', 'size',
            'dimension', 'thumbnail'
        )

    def get_attachment(self, obj):
        im_url = get_attachment_url(obj, os.path.split(obj.attachment.name)[1])
        return im_url

    def get_thumbnail(self, obj):
        return obj.thumbnail()

    def get_size(self, obj):
        return obj.attachment.size

    def get_dimension(self, obj):
        try:
            im = Image.open(obj.attachment.name)
            return im.size
        except:
            pass

        return None
