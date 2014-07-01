import os
import shutil

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.core.validators import RegexValidator, MinLengthValidator

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


class AddPersonForm(BaseControlForm, forms.ModelForm):
    username = forms.CharField(
            label=_('Username'),
            required=True, 
            error_messages={
                'required': _('Username is required.'),
                'ivalid': _("Illegal characters in username.")
            },
            max_length=100, 
            validators=[
                RegexValidator(r"^[\w\d\@\.\+\-\_]+$", message=_("Illegal characters in username.")), 
                MinLengthValidator(3)
            ]
        )
    first_name = forms.CharField(
            label=_('First name'),
            required=True, 
            error_messages={'required': _('First name is required.')},                                 
            max_length=32
        )
    email = forms.EmailField(
            label=_('Email'),
            required=True,
            error_messages={'required': _('Email is required.')},                                 
            max_length=100
        )
    description = forms.CharField(
            label=_("User description"), 
            required=False, 
            widget=forms.Textarea
        )
    password1 = forms.CharField(
            label=_('Password'), 
            required=True, 
            error_messages={'required': _('Password is required.')},
            max_length=100, 
            widget=forms.PasswordInput
        )
    password2 = forms.CharField(
            label=_('Password confirmation'), 
            required=True, 
            error_messages={'required': _('Password is required.')},
            max_length=100, 
            widget=forms.PasswordInput, 
            help_text = _("Enter the same password as above, for verification.")
        )
    send_email = forms.BooleanField(
            label=_('Notify person by email'), 
            required=False
        )

    success_message = _('Successfuly created new account.')

    class Meta:
        model = User
        exclude = [
            'password', 'is_superuser',
            'last_login', 'groups',
            'user_permissions', 'date_joined',
            'is_staff', 'last_name', 'is_active'
        ]

    def clean_username(self):
        try:
            User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_("This Person already exists."))

        return self.cleaned_data['username']

    def clean_password2(self):
        if self.cleaned_data['password2'] != self.cleaned_data['password1']:
            raise forms.ValidationError(_("Passwords do not match."))

        return self.cleaned_data['password2']
    
    def save_settings(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password2']
        )
        user.first_name = self.cleaned_data['first_name']
        user.save()

        user.get_profile().description = self.cleaned_data['description']
        user.get_profile().save()

        # TODO: create a signal for this and move to right place
        if self.cleaned_data["send_email"]:
            from django import template

            t = template.loader.get_template('booktypecontrol/new_person_email.html')
            content = t.render(template.Context({"username": self.cleaned_data['username'],
                                                 "password": self.cleaned_data['password2'],
                                                 "server":   settings.BOOKTYPE_URL}))

            from django.core.mail import EmailMultiAlternatives
            emails = [self.cleaned_data['email']]

            msg = EmailMultiAlternatives('You have a new Booktype Account ', content, settings.REPORT_EMAIL_USER, emails)
            msg.attach_alternative(content, "text/html")
            msg.send(fail_silently=True)

        return user


class ListOfPeopleForm(BaseControlForm, forms.Form):
    pass

    @classmethod
    def extra_context(cls):
        return {
            'people': User.objects.all().order_by("username")
        }


class EditPersonInfoForm(BaseControlForm, forms.ModelForm):
    username = forms.CharField(
            label=_('Username'),
            required=True, 
            max_length=100, 
            error_messages={'required': _('Username is required.'),
                           'ivalid': _("Illegal characters in username.")},
            validators=[
                RegexValidator(r"^[\w\d\@\.\+\-\_]+$", message=_("Illegal characters in username.")), 
                MinLengthValidator(3)
            ]
        )
    first_name = forms.CharField(
            label=_('First name'),
            required=True, 
            error_messages={'required': _('First name is required.')},                                 
            max_length=32
        )
    email = forms.EmailField(
            label=_('Email'),
            required=True,
            error_messages={'required': _('Email is required.')},                                 
            max_length=100
        )
    profile = forms.ImageField(
            label=_('Profile picture'),
            required=False
        )
    description = forms.CharField(
            label=_("User description"), 
            required=False, 
            widget=forms.Textarea
        )

    class Meta(AddPersonForm.Meta):
        pass        

# TODO: remove after completing new control center
ProfileForm = EditPersonInfoForm


class PasswordForm(BaseControlForm, forms.Form):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    password1 = forms.CharField(
            label=_('Password'), 
            required=True, 
            error_messages={'required': _('Password is required.')},
            max_length=100, 
            widget=forms.PasswordInput
        )
    password2 = forms.CharField(
            label=_('Password confirmation'), 
            required=True, 
            max_length=100, 
            error_messages={'required': _('Password is required.')},
            widget=forms.PasswordInput, 
            help_text = _("Enter the same password as above, for verification.")
        )

    def __init__(self, user, *args, **kwargs):
            self.user = user
            super(PasswordForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['password1'])
        if commit:
            self.user.save()
        return self.user
