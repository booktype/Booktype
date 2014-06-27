import os
import shutil

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _

from booktype.apps.core.forms import BaseBooktypeForm
from booktype.utils import config
from booki.utils import misc
from booki.editor.models import License

class BaseControlForm(BaseBooktypeForm):
    """
    Base class for Control Center forms
    """
    success_message = None

    @classmethod
    def initial_data(cls):
        return None

    @classmethod
    def extra_context(cls):
        return {}

    def save_settings(self):
        pass

class SiteDescriptionForm(BaseControlForm, forms.Form):
    title = forms.CharField(
            label=_("Site title"),
            required=True, 
            error_messages={'required': _('Site title is required.')},
            max_length=200
        )
    tagline = forms.CharField(
            label=_("Tagline"), 
            required=False,
            max_length=200
        )
    favicon = forms.FileField(
            label=_("Favicon"), 
            required=False, 
            help_text=_("Upload .ico file")
        )

    @classmethod
    def initial_data(cls):
        return {
            'title': config.get_configuration('BOOKTYPE_SITE_NAME'),
            'tagline': config.get_configuration('BOOKTYPE_SITE_TAGLINE')
        }

    def save_settings(self):
        config.set_configuration('BOOKTYPE_SITE_NAME', self.cleaned_data['title'])
        config.set_configuration('BOOKTYPE_SITE_TAGLINE', self.cleaned_data['tagline'])

        if self.files.has_key('favicon'):
            # just check for any kind of silly error
            try:
                fh, fname = misc.saveUploadedAsFile(self.files['favicon'])
                shutil.move(fname, '%s/favicon.ico' % settings.STATIC_ROOT)

                config.set_configuration('BOOKTYPE_SITE_FAVICON', '%s/static/favicon.ico' % settings.BOOKTYPE_URL)
            except:
                pass

        try:
            config.save_configuration()
        except config.ConfigurationError as err:
            raise err


class AppearanceForm(BaseControlForm, forms.Form):
    css = forms.CharField(
            label=_('CSS'),
            required=False,
            widget=forms.Textarea(attrs={'rows': 20, 'cols': 40})
        )

    @classmethod
    def initial_data(cls):
        try:
            f = open('%s/css/_user.css' % settings.STATIC_ROOT, 'r')
            css_content = unicode(f.read(), 'utf8')
            f.close()
        except IOError:
            css_content = ''

        return dict(css=css_content)

    def save_settings(self):
        try:
            # should really save it in a safe way
            f = open('%s/css/_user.css' % settings.STATIC_ROOT, 'w')
            f.write(self.cleaned_data['css'].encode('utf8'))
            f.close()
        except IOError as err:
            raise err


class FrontpageForm(BaseControlForm, forms.Form):
    description = forms.CharField(
            label=_('Welcome message'),
            required=False, 
            widget=forms.Textarea(attrs={'rows': 20, 'cols': 40})
        )
    show_changes = forms.BooleanField(
            label=_('Show activity'), 
            required=False
        )

    @classmethod
    def initial_data(cls):
        _dict = {}
        try:
            f = open('%s/templates/portal/welcome_message.html' % settings.BOOKTYPE_ROOT, 'r')
            _dict['description'] = unicode(f.read(), 'utf8')
            f.close()
        except IOError:
            _dict['description'] = ''

        _dict['show_changes'] = config.get_configuration('BOOKTYPE_FRONTPAGE_HISTORY', True)
        return _dict

    def save_settings(self):
        staticRoot = settings.BOOKTYPE_ROOT
        config.set_configuration('BOOKTYPE_FRONTPAGE_HISTORY', self.cleaned_data['show_changes'])

        if not os.path.exists('%s/templates/portal/' % staticRoot):
            os.makedirs('%s/templates/portal/' % staticRoot)

        try:
            f = open('%s/templates/portal/welcome_message.html' % staticRoot, 'w')
            
            text_data = self.cleaned_data.get('description', '')
            text_data = text_data.replace('{%', '').replace('%}', '').replace('{{', '').replace('}}', '')

            f.write(text_data.encode('utf8'))
            f.close()
            config.save_configuration()

        except IOError as err:
            raise err
        except config.ConfigurationError as err:
            raise err


class LicenseForm(BaseControlForm, forms.ModelForm):
    abbrevation = forms.CharField(
            label=_("Abbrevation"),
            required=True, 
            error_messages={'required': _('Abbrevation is required.')},
            max_length=30
        )
    name = forms.CharField(
            label=_("Name"),
            required=True,
            error_messages={'required': _('License name is required.')},                                                            
            max_length=100
        )

    success_message = _('Succesfully created new license.')

    class Meta:
        model = License

    @classmethod
    def extra_context(cls):
        return dict(licenses=License.objects.all().order_by("name"))

    def save_settings(self):
        return self.save()


class BookSettingsForm(BaseControlForm, forms.Form):
    visible = forms.BooleanField(
            label=_('Default visibility'), 
            required=False, 
            help_text=_('If it is turned on then all books will be visible to everyone.')
        )
    license = forms.ModelChoiceField(
            label=_('Default License'), 
            queryset=License.objects.all().order_by("name"), 
            required=False,
            help_text=_("Default license for newly created books.")
        )

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)

    @classmethod
    def initial_data(self):
        _l = config.get_configuration('CREATE_BOOK_LICENSE')
        if _l and _l != '':
            try:
                license = License.objects.get(abbrevation = _l)
            except License.DoesNotExist:
                license = None
        else:
            license = None

        return {
            'visible': config.get_configuration('CREATE_BOOK_VISIBLE'), 
            'license': license
        }

    def save_settings(self):
        config.set_configuration('CREATE_BOOK_VISIBLE', self.cleaned_data['visible'])

        if 'license' in self.cleaned_data:
            config.set_configuration('CREATE_BOOK_LICENSE', self.cleaned_data['license'].abbrevation)
        else:
            config.set_configuration('CREATE_BOOK_LICENSE', '')

        try:
            config.save_configuration()
        except config.ConfigurationError as err:
            raise err

# TODO: to be removed at same time of
# old control center code
BookCreateForm = BookSettingsForm


class PrivacyForm(BaseControlForm, forms.Form):
    user_register = forms.BooleanField(
            label=_('Anyone can register'), 
            required=False, 
            help_text=_('Anyone can register on the site and create account')
        )
    create_books = forms.BooleanField(
            label=_('Only admin can create books'), 
            required=False
        )
    import_books = forms.BooleanField(
            label=_('Only admin can import books'), 
            required=False
        )

    # overriding init to remove field css classes from BaseControlForm
    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)

    @classmethod
    def initial_data(cls):
        return {
            'user_register': config.get_configuration('FREE_REGISTRATION'),
            'create_books': config.get_configuration('ADMIN_CREATE_BOOKS'),
            'import_books': config.get_configuration('ADMIN_IMPORT_BOOKS')
        }

    def save_settings(self):
        config.set_configuration('FREE_REGISTRATION', self.cleaned_data['user_register'])
        config.set_configuration('ADMIN_CREATE_BOOKS', self.cleaned_data['create_books'])
        config.set_configuration('ADMIN_IMPORT_BOOKS', self.cleaned_data['import_books'])

        try:
            config.save_configuration()            
        except config.ConfigurationError as err:
            raise err