# -*- coding: utf-8 -*-
import sys
import json
import logging

from django import forms
from django.conf import settings
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from booktype.utils import security, config
from booktypecontrol.forms import DefaultRolesForm
from booktype.apps.portal.forms import SpanErrorList
from booktype.apps.core.models import BookRole, Role
from booktype.apps.core.forms import BaseBooktypeForm
from booki.editor.models import (
    Language, Info, License, BookSetting, BookStatus)

from booki.editor.models import METADATA_FIELDS

from .models import InviteCode

logger = logging.getLogger('booktype.apps.edit.forms')


class BaseSettingsForm(BaseBooktypeForm):
    success_url = None
    success_message = None
    required_permission = None

    def __init__(self, *args, **kwargs):
        kwargs.update({'error_class': SpanErrorList})
        self.book = kwargs.pop('book')
        super(BaseSettingsForm, self).__init__(*args, **kwargs)

    @classmethod
    def initial_data(cls, book=None, request=None):
        return None

    @classmethod
    def extra_context(cls, book=None, request=None):
        return {}

    @classmethod
    def has_perm(cls, book=None, request=None):
        if cls.required_permission:
            book_security = security.get_security_for_book(request.user, book)
            return book_security.has_perm(cls.required_permission)

        # if there no required permission, then True
        return True

    def save_settings(self, request):
        pass


class LanguageForm(BaseSettingsForm, forms.Form):
    language = forms.ModelChoiceField(
        label=_('Language'),
        queryset=Language.objects.all().order_by('name')
    )
    right_to_left = forms.BooleanField(
        label=_('Right to left text'),
        required=False,
        help_text=_("Book with right to left writing.")
    )
    skip_select_and_checkbox = True
    required_permission = 'edit.manage_language'

    @classmethod
    def initial_data(cls, book=None, request=None):
        try:
            rtl = Info.objects.get(book=book, kind=0, name='{http://booki.cc/}dir').getValue()
        except (Info.DoesNotExist, Info.MultipleObjectsReturned):
            rtl = 'LTR'

        return {
            'right_to_left': (rtl == 'RTL'),
            'language': book.language
        }

    def save_settings(self, book, request):
        book.language = self.cleaned_data['language']
        book.save()

        rtl_value = self.cleaned_data['right_to_left']
        rtl_value = "RTL" if rtl_value else "LTR"

        try:
            rtl = Info.objects.get(book=book, kind=0, name='{http://booki.cc/}dir')
            rtl.value_string = rtl_value
            rtl.save()
        except Info.DoesNotExist:
            rtl = Info(book=book, kind=0, name='{http://booki.cc/}dir', value_string=rtl_value)
            rtl.save()

        return {'dir': rtl_value.lower(),
                'lang': book.language.abbrevation if book.language else 'en'}


class GeneralForm(BaseSettingsForm, forms.Form):
    track_changes = forms.BooleanField(
        label=_('Track changes'),
        required=False,
        help_text=_("Chapter changes will tracked.")
    )
    required_permission = 'edit.manage_book_settings'

    @classmethod
    def initial_data(cls, book=None, request=None):
        data = {}
        book_version = book.get_version()

        if book_version:
            data['track_changes'] = book_version.track_changes

        return data

    def save_settings(self, book, request):
        book_version = book.get_version()
        book_version.track_changes = self.cleaned_data['track_changes']
        book_version.save()


class ChapterStatusForm(BaseSettingsForm, forms.Form):
    name = forms.CharField(label=_('New Status'))
    required_permission = 'edit.manage_status'

    @classmethod
    def extra_context(cls, book, request):
        from .channel import get_book_statuses_dict

        return {
                'roles_permissions': security.get_user_permissions(request.user, book),
                'status_list': get_book_statuses_dict(book)
            }


class LicenseForm(BaseSettingsForm, forms.Form):
    license = forms.ModelChoiceField(
        label=_('License'),
        queryset=License.objects.all().order_by("name")
    )
    skip_select_and_checkbox = True
    required_permission = 'edit.manage_license'

    @classmethod
    def initial_data(cls, book=None, request=None):
        return {
            'license': book.license
        }

    def save_settings(self, book, request):
        book.license = self.cleaned_data['license']
        book.save()

    def license_list(self):
        license_dict = {}
        for val in License.objects.all().values('id', 'url'):
            license_dict[val['id']] = val['url']
        return json.dumps(license_dict)


class ChapterStatus(BaseSettingsForm, forms.Form):
    pass


class MetadataForm(BaseSettingsForm, forms.Form):

    required_permission = 'edit.manage_metadata'

    def __init__(self, *args, **kwargs):
        super(MetadataForm, self).__init__(*args, **kwargs)

        for field, label, standard in METADATA_FIELDS:
            field_name = '%s.%s' % (standard, field)
            self.fields[field_name] = forms.CharField(
                label=label, required=False)

            c_field = self.fields[field_name]
            BaseBooktypeForm.apply_class(c_field, 'form-control')

            # apply widgets if needed
            if field in self.Meta.widgets:
                c_field.widget = self.Meta.widgets[field]

    class Meta:
        text_area = forms.Textarea(attrs={'class': 'form-control'})
        widgets = {
            'short_description': text_area,
            'long_description': text_area
        }

    @classmethod
    def initial_data(cls, book=None, request=None):
        initial = {}
        form_fields = ['%s.%s' % (f[2], f[0]) for f in METADATA_FIELDS]

        for meta in Info.objects.filter(book=book):
            if meta.name in form_fields:
                initial[meta.name] = meta.value_string

        return initial

    def save_settings(self, book, request):
        _string = 0

        for key, value in self.cleaned_data.items():
            valid_value = self.cleaned_data.get(key, None)

            if key in self.fields.keys() and valid_value:
                meta, _ = Info.objects.get_or_create(
                    book=book, name=key,
                    kind=_string
                )

                meta.value_string = value
                meta.save()


class AdditionalMetadataForm(BaseSettingsForm, forms.Form):
    required_permission = 'edit.manage_metadata'
    META_PREFIX = 'ADD_META_TERMS'  # noqa

    def __init__(self, *args, **kwargs):
        super(AdditionalMetadataForm, self).__init__(*args, **kwargs)
        book = kwargs.get('book')
        additional_fields = getattr(settings, 'ADDITIONAL_METADATA', {})

        for field, attrs in additional_fields.items():
            field_name = '%s.%s' % (self.META_PREFIX, field)
            try:
                if 'TYPE' not in attrs.keys():
                    logger.error(
                        _('%(field)s must have TYPE attribute') % {'field': field})
                    continue

                field_class = getattr(forms, attrs.get('TYPE'))
                field_attrs = attrs.get('ATTRS', {})
                default_widget = field_class.widget.__name__

                widget_class = getattr(forms.widgets, attrs.get('WIDGET', default_widget))
                widget_atts = attrs.get('WIDGET_ATTRS', {})

                # build the widget
                field_attrs['widget'] = widget_class(attrs=widget_atts)
                field_attrs['label'] = field_attrs.get('label', field.title())

                # now create the field
                self.fields[field_name] = field_class(**field_attrs)

                # add bootstrap class if is not choice field
                if attrs.get('TYPE') != 'ChoiceField':
                    c_field = self.fields[field_name]
                    BaseBooktypeForm.apply_class(c_field, 'form-control')

            except Exception as err:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error(
                    _('Unable to create field %(field)s. Reason: %(error)s | type: %(exc_type)s | Line: %(line_no)s ') %
                    {
                        'field': field, 'error': err,
                        'exc_type': exc_type, 'line_no': exc_tb.tb_lineno
                    }
                )

        # maybe we should move this later if needed
        def unslugify(value):
            return value.replace('-', ' ').replace('_', ' ')

        # now add the stored field
        for meta in Info.objects.filter(book=book, name__startswith=self.META_PREFIX).order_by('id'):
            keyname = meta.name.split('.')[1]
            if keyname not in additional_fields.keys():
                self.fields[meta.name] = forms.CharField(
                    widget=forms.widgets.Textarea(attrs={'class': 'form-control meta-dynamic in_db'}),
                    label=unslugify(keyname.capitalize())
                )

    @property
    def max_limit(self):
        return config.get_configuration('MAX_ADDITIONAL_METADATA', 3)

    @property
    def limit_reached(self):
        dynamics = [1 for x in self.fields.values() if 'meta-dynamic' in x.widget.attrs.get('class', '')]
        return (len(dynamics) >= self.max_limit)

    @classmethod
    def initial_data(cls, book=None, request=None):
        initial = {}

        for meta in Info.objects.filter(book=book, name__startswith=cls.META_PREFIX):
            json_dec = json.decoder.JSONDecoder()
            field_value = meta.value_string

            try:
                field_value = json_dec.decode(meta.value_string)
                # for now we just care about list types
                # otherwise, exclude the value
                if not isinstance(field_value, list):
                    field_value = meta.value_string
            except Exception:
                pass

            initial[meta.name] = field_value
        return initial

    def save_settings(self, book, request):
        form_fields = getattr(settings, 'ADDITIONAL_METADATA', {})
        limit = self.max_limit
        _string = 0
        counter = 0

        for key, value in request.POST.items():
            if (self.META_PREFIX in key) and (counter < limit):
                meta, _ = Info.objects.get_or_create(
                    book=book, name=key,
                    kind=_string
                )

                # check the limit for dinamically added fields
                if key.split('.')[1] not in form_fields:
                    counter += 1

                # we need to check certain type of field and treat them other way
                # MultipleChoiceField for instance
                _key = key.split('.')[1]
                if form_fields.get(_key, {}).get('TYPE') == 'MultipleChoiceField':
                    try:
                        raw_list = request.POST.getlist(key)
                        value = json.dumps(raw_list)
                    except Exception as err:
                        logger.error('Unable to save the value `%s` for field %s, err: %s' % (value, key, err))
                        meta.delete()
                        continue

                meta.value_string = value
                meta.save()


class RolesForm(BaseSettingsForm, forms.Form):
    required_permission = 'core.manage_roles'

    @classmethod
    def extra_context(cls, book, request):
        member_ids = book.bookrole_set.all().values_list('members', flat=True)
        default_roles = getattr(settings, 'BOOKTYPE_DEFAULT_ROLES', {})

        return {
            'book_users': User.objects.filter(id__in=member_ids).order_by('username'),
            'roles': Role.objects.exclude(name__in=default_roles.keys()),
            'user': request.user
        }


class PermissionsForm(BaseSettingsForm, DefaultRolesForm):
    skip_select_and_checkbox = True
    required_permission = 'core.manage_permissions'

    @classmethod
    def initial_data(cls, book=None, request=None):
        initial = DefaultRolesForm.initial_data()

        for role_name in [cls.anonymous, cls.registered]:
            try:
                initial[role_name] = BookSetting.objects.get(
                    book=book, name='DEFAULT_ROLE_%s' % role_name
                ).get_value()
            except:
                pass

        return initial

    def save_settings(self, book, request):
        STRING = 0  # noqa

        for key in [self.anonymous, self.registered]:
            value = self.cleaned_data.get(key, None)
            role_key = 'DEFAULT_ROLE_%s' % key
            if value:
                setting, _ = BookSetting.objects.get_or_create(
                    book=book, name=role_key, kind=STRING
                )
                setting.value_string = value
                setting.save()


class InviteCodeForm(BaseBooktypeForm, forms.ModelForm):
    default_roles = getattr(settings, 'BOOKTYPE_DEFAULT_ROLES', {})

    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.exclude(name__in=default_roles.keys()))
    expire_on = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        model = InviteCode
        fields = ['roles', 'expire_on']
