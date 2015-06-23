import os
import shutil
import logging

from django import forms
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator, MinLengthValidator

from booktype.utils import config
from booktype.apps.account.models import UserProfile
from booktype.apps.core.forms import BaseBooktypeForm
from booktype.apps.core.models import Role, Permission
from booktype.apps.core.widgets import GroupedCheckboxSelectMultiple
from booktype.apps.portal.forms import GroupCreateForm
from booktype.apps.portal.widgets import RemovableImageWidget

from booktype.utils import misc
from booki.editor.models import License, Book, BookiGroup
from booktype.utils.book import (
    create_book, rename_book, check_book_availability
)

logger = logging.getLogger('booktype')


class BaseControlForm(BaseBooktypeForm):
    """
    Base class for Control Center forms
    """
    success_message = None
    success_url = None
    cancel_url = reverse_lazy('control_center:settings')

    @classmethod
    def initial_data(cls):
        return None

    @classmethod
    def extra_context(cls):
        return {}

    def get_cancel_url(self):
        return self.cancel_url

    def save_settings(self, request):
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

    def save_settings(self, request):
        config.set_configuration(
            'BOOKTYPE_SITE_NAME', self.cleaned_data['title'])
        config.set_configuration(
            'BOOKTYPE_SITE_TAGLINE', self.cleaned_data['tagline'])

        if 'favicon' in self.files:
            # just check for any kind of silly error
            try:
                fh, fname = misc.save_uploaded_as_file(self.files['favicon'])
                shutil.move(fname, '%s/favicon.ico' % settings.STATIC_ROOT)

                config.set_configuration(
                    'BOOKTYPE_SITE_FAVICON',
                    '%s/static/favicon.ico' % settings.BOOKTYPE_URL
                )
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

    def save_settings(self, request):
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
    use_anonymous_page = forms.BooleanField(
        label=_('Use anonymous page'),
        required=False,
        help_text=_('Use separate page for anonymous users without books, '
                    'people, groups and recent activity blocks.')
    )
    anonymous_message = forms.CharField(
        label=_('Anonymous page message'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 40}),
        help_text=_('Message for displaying on anonymous page.')
    )
    anonymous_email = forms.EmailField(
        label=_('Anonymous page email'),
        required=False,
        help_text=_('Email for displaying on anonymous page.')
    )
    anonymous_image = forms.ImageField(
        label=_("Anonymous page image"),
        required=False,
        help_text=_("Use image/png files."),
        widget=RemovableImageWidget(attrs={
            'label_class': 'checkbox-inline',
            'input_class': 'group-image-removable'
        })
    )

    def clean_anonymous_image(self):
        data = self.cleaned_data['anonymous_image']
        if data and data.content_type not in ['image/png']:
            raise forms.ValidationError("Wrong file content type.")
        return data

    @classmethod
    def initial_data(cls):
        _dict = {}
        try:
            f = open(
                '%s/templates/portal/welcome_message.html'
                % settings.BOOKTYPE_ROOT,
                'r'
            )
            _dict['description'] = unicode(f.read(), 'utf8')
            f.close()
        except IOError:
            _dict['description'] = ''

        _dict['show_changes'] = config.get_configuration('BOOKTYPE_FRONTPAGE_HISTORY', True)
        _dict['use_anonymous_page'] = config.get_configuration('BOOKTYPE_FRONTPAGE_USE_ANONYMOUS_PAGE')
        _dict['anonymous_message'] = config.get_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_MESSAGE')
        _dict['anonymous_email'] = config.get_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_EMAIL')
        _dict['anonymous_image'] = config.get_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_IMAGE')

        return _dict

    def save_settings(self, request):
        static_root = settings.BOOKTYPE_ROOT

        config.set_configuration('BOOKTYPE_FRONTPAGE_HISTORY', self.cleaned_data['show_changes'])
        config.set_configuration('BOOKTYPE_FRONTPAGE_USE_ANONYMOUS_PAGE', self.cleaned_data['use_anonymous_page'])
        config.set_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_MESSAGE', self.cleaned_data['anonymous_message'])
        config.set_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_EMAIL', self.cleaned_data['anonymous_email'])

        # anonymous page image
        destination_filename = 'anonymous_image.png'
        destination_dir = '{0}/portal/frontpage/'.format(settings.MEDIA_ROOT)
        destination_file_path = '{dir}{filename}'.format(dir=destination_dir, filename=destination_filename)

        if 'anonymous_image_remove' in request.POST:
            os.remove(destination_file_path)
            config.del_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_IMAGE')
        elif 'anonymous_image' in self.files:
            try:
                fh, fname = misc.save_uploaded_as_file(self.files['anonymous_image'])

                if not os.path.exists(destination_dir):
                    os.makedirs(destination_dir)

                shutil.move(fname, destination_file_path)
                config.set_configuration('BOOKTYPE_FRONTPAGE_ANONYMOUS_IMAGE',
                                         '{0}portal/frontpage/anonymous_image.png'.format(settings.MEDIA_URL))
            except:
                pass

        # welcome message
        if not os.path.exists('%s/templates/portal/' % static_root):
            os.makedirs('%s/templates/portal/' % static_root)

        try:
            f = open(
                '%s/templates/portal/welcome_message.html' % static_root, 'w')

            text_data = self.cleaned_data.get('description', '')
            for ch in ['{%', '%}', '{{', '}}']:
                text_data = text_data.replace(ch, '')

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
    url = forms.URLField(
        label=_("License URL"),
        required=True,
        error_messages={'required': _('License name is required.')},
        max_length=200
    )

    success_message = _('Succesfully created new license.')
    success_url = "#license"

    class Meta:
        model = License
        fields = '__all__'

    @classmethod
    def extra_context(cls):
        return dict(licenses=License.objects.all().order_by("name"))

    def get_cancel_url(self):
        return "{0}{1}".format(self.cancel_url, self.success_url)

    def save_settings(self, request):
        return self.save()


class BookSettingsForm(BaseControlForm, forms.Form):
    hlp_visible = 'If it is turned on then all\
        books will be visible to everyone.'
    visible = forms.BooleanField(
        label=_('Default visibility'),
        required=False,
        help_text=_(hlp_visible)
    )
    license = forms.ModelChoiceField(
        label=_('Default License'),
        queryset=License.objects.all().order_by("name"),
        required=False,
        help_text=_("Default license for newly created books.")
    )

    @classmethod
    def initial_data(cls):
        _l = config.get_configuration('CREATE_BOOK_LICENSE')
        if _l and _l != '':
            try:
                license = License.objects.get(abbrevation=_l)
            except License.DoesNotExist:
                license = None
        else:
            license = None

        return {
            'visible': config.get_configuration('CREATE_BOOK_VISIBLE'),
            'license': license
        }

    def save_settings(self, request):
        config.set_configuration(
            'CREATE_BOOK_VISIBLE', self.cleaned_data['visible'])

        if 'license' in self.cleaned_data:
            config.set_configuration(
                'CREATE_BOOK_LICENSE',
                self.cleaned_data['license'].abbrevation
            )
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

    @classmethod
    def initial_data(cls):
        return {
            'user_register': config.get_configuration('FREE_REGISTRATION'),
            'create_books': config.get_configuration('ADMIN_CREATE_BOOKS'),
            'import_books': config.get_configuration('ADMIN_IMPORT_BOOKS')
        }

    def save_settings(self, request):
        config.set_configuration(
            'FREE_REGISTRATION', self.cleaned_data['user_register'])
        config.set_configuration(
            'ADMIN_CREATE_BOOKS', self.cleaned_data['create_books'])
        config.set_configuration(
            'ADMIN_IMPORT_BOOKS', self.cleaned_data['import_books'])

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
            RegexValidator(
                r"^[\w\d\@\.\+\-\_]+$",
                message=_("Illegal characters in username.")
            ),
            MinLengthValidator(3)
        ]
    )
    first_name = forms.CharField(
        label=_('Full name'),
        required=True,
        error_messages={'required': _('Full name is required.')},
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
        help_text=_("Enter the same password as above, for verification.")
    )
    send_email = forms.BooleanField(
        label=_('Notify person by email'),
        required=False
    )

    is_superuser = forms.BooleanField(
        label=_("This person is superuser"),
        required=False
    )

    success_message = _('Successfully created new account.')
    success_url = "#list-of-people"

    def __init__(self, *args, **kwargs):
        super(AddPersonForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['username', 'first_name', 'email',
                                'description', 'password1', 'password2',
                                'send_email', 'is_superuser']

    class Meta:
        model = User
        exclude = [
            'password', 'last_login', 'groups',
            'user_permissions', 'date_joined',
            'is_staff', 'last_name', 'is_active'
        ]

    def get_cancel_url(self):
        return "{0}{1}".format(self.cancel_url, self.success_url)

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

    def save_settings(self, request):
        user_data = dict(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password2'],
        )
        if self.cleaned_data.get('is_superuser', False):
            user = User.objects.create_superuser(**user_data)
        else:
            user = User.objects.create_user(**user_data)

        user.first_name = self.cleaned_data['first_name']
        user.save()

        profile = UserProfile.objects.get_or_create(user=user)[0]
        profile.description = self.cleaned_data['description']
        profile.save()

        if self.cleaned_data.get('send_email', False):
            from django import template

            t = template.loader.get_template(
                'booktypecontrol/new_person_email.html')
            content = t.render(template.Context({
                "username": self.cleaned_data['username'],
                "password": self.cleaned_data['password2'],
                "server": settings.BOOKTYPE_URL
            }))

            from django.core.mail import EmailMultiAlternatives
            emails = [self.cleaned_data['email']]

            msg = EmailMultiAlternatives(
                'You have a new Booktype Account',
                content, settings.REPORT_EMAIL_USER, emails
            )
            msg.attach_alternative(content, "text/html")
            try:
                msg.send(fail_silently=False)
            except Exception as e:
                logger.error(
                    '[CCENTER] Unable to send invite email to %s msg: %s' %
                    (self.cleaned_data['email'], e)
                )

        return user


class ListOfPeopleForm(BaseControlForm, forms.Form):
    pass

    @classmethod
    def extra_context(cls):
        return {
            'people': User.objects.all().order_by("username")
        }


class ArchivedUsersForm(BaseControlForm, forms.Form):
    pass

    @classmethod
    def extra_context(cls):
        return {
            'archived_people': User.objects.filter(is_active=False).order_by("username")
        }

class EditPersonInfoForm(BaseControlForm, forms.ModelForm):
    username = forms.CharField(
        label=_('Username'),
        required=True,
        max_length=100,
        error_messages={
            'required': _('Username is required.'),
            'ivalid': _("Illegal characters in username.")
        },
        validators=[
            RegexValidator(
                r"^[\w\d\@\.\+\-\_]+$",
                message=_("Illegal characters in username.")
            ),
            MinLengthValidator(3)
        ]
    )
    first_name = forms.CharField(
        label=_('Full name'),
        required=True,
        error_messages={'required': _('Full name is required.')},
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
        required=False,
        widget=RemovableImageWidget(attrs={
            'label_class': 'checkbox-inline',
            'input_class': 'group-image-removable'
        })
    )
    description = forms.CharField(
        label=_("User description"),
        required=False,
        widget=forms.Textarea
    )

    is_superuser = forms.BooleanField(
        label=_("This person is superuser"),
        required=False
    )
    is_active = forms.BooleanField(
        label=_("Active account"),
        required=False,
        help_text=_("Indicate whether user's account is archived or active.")
    )

    def __init__(self, *args, **kwargs):
        super(EditPersonInfoForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['username', 'first_name', 'email',
                                'description', 'is_superuser']

    class Meta:
        model = User
        exclude = [
            'password', 'last_login', 'groups',
            'user_permissions', 'date_joined',
            'is_staff', 'last_name'
        ]

    def get_cancel_url(self):
        return "{0}#list-of-people".format(self.cancel_url)


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
        help_text=_("Enter the same password as above, for verification.")
    )
    send_login_data = forms.BooleanField(
        label=_('Send login data'),
        required=False,
        help_text=_('Send new login data to the user via email.'),
        initial=True
    )
    short_message = forms.CharField(
        label=_('Short message'),
        required=False,
        help_text=_('Will be added in the bottom of email message text, after new user credentials.'),
        widget=forms.Textarea(attrs={'rows': 4}),
        initial=_('You can change password in your profile settings page.')
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


class AddBookForm(BaseControlForm, forms.Form):
    title = forms.CharField(
        label=_("Title"),
        error_messages={'required': _('Title is required.')},
        required=True,
        max_length=100
    )
    description = forms.CharField(
        label=_('Description'),
        required=False,
        widget=forms.Textarea
    )
    owner = forms.ModelChoiceField(
        label=_('Owner'),
        error_messages={'required': _('Book owner is required.')},
        queryset=User.objects.all().order_by("username"),
        required=True
    )
    license = forms.ModelChoiceField(
        label=_('License'),
        queryset=License.objects.all().order_by("name"),
        error_messages={'required': _('License is required.')},
        required=True
    )
    is_hidden = forms.BooleanField(
        label=_('Initially hide from others'),
        required=False
    )
    cover = forms.ImageField(
        label=_('Book image'),
        required=False
    )

    success_message = _('Successfully created new book.')

    def clean_title(self):
        if not check_book_availability(self.cleaned_data['title']):
            raise forms.ValidationError(_("This Book already exists."))
        return self.cleaned_data['title']

    def save_settings(self, request):
        book = create_book(
            self.cleaned_data['owner'],
            self.cleaned_data['title']
        )
        book.license = self.cleaned_data['license']
        book.description = self.cleaned_data['description']
        book.hidden = self.cleaned_data['is_hidden']
        book.save()

        if 'cover' in self.files:
            try:
                fh, fname = misc.save_uploaded_as_file(self.files['cover'])
                book.set_cover(fname)
                os.unlink(fname)
            except:
                pass

        book.save()

        return book


class ListOfBooksForm(BaseControlForm, forms.Form):
    pass

    @classmethod
    def extra_context(cls):
        return {
            'books': Book.objects.all().order_by("title")
        }


class BookRenameForm(BaseControlForm, forms.ModelForm):
    title = forms.CharField(
        label=_("Title"),
        required=True,
        error_messages={'required': _('Title is required.')},
        max_length=200
    )
    url_title = forms.SlugField(
        label=_("URL title"),
        required=False,
        max_length=200,
        error_messages={'invalid': _("Illegal characters in URL title.")},
        help_text=_("If you leave this field empty URL\
        title will be assigned automatically.")
    )

    class Meta:
        model = Book
        exclude = [
            'status', 'language',
            'version', 'group',
            'created', 'published',
            'permission', 'cover',
            'description', 'hidden',
            'owner', 'license'
        ]
        fields = ['title', 'url_title']

    def get_cancel_url(self):
        return "{0}#list-of-books".format(self.cancel_url)

    def save(self, *args, **kwargs):
        if self.instance.pk and self.has_changed():
            book = Book.objects.get(url_title__iexact=self.initial['url_title'])
            rename_book(
                book,
                self.cleaned_data['title'],
                self.cleaned_data['url_title']
            )
        return super(BookRenameForm, self).save(*args, **kwargs)

    def clean_url_title(self):
        url_title = self.cleaned_data['url_title']
        if not url_title:
            return misc.booktype_slugify(self.cleaned_data['title'])
        return url_title


class PublishingForm(BaseControlForm, forms.Form):
    OPTIONS = ('mpdf', 'screenpdf', 'epub', 'mobi', 'xhtml')

    publish_mpdf = forms.BooleanField(
        label=_('Book PDF'),
        required=False
    )
    publish_screenpdf = forms.BooleanField(
        label=_('Screen PDF'),
        required=False
    )
    publish_epub = forms.BooleanField(
        label=_('EPUB'),
        required=False
    )
    publish_mobi = forms.BooleanField(
        label=_('MOBI'),
        required=False
    )
    publish_xhtml = forms.BooleanField(
        label=_('XHTML'),
        required=False
    )

    @classmethod
    def initial_data(cls):
        publish_options = config.get_configuration('PUBLISH_OPTIONS')

        return {
            'publish_mpdf': 'mpdf' in publish_options,
            'publish_screenpdf': 'screenpdf' in publish_options,
            'publish_epub': 'epub' in publish_options,
            'publish_mobi': 'mobi' in publish_options,
            'publish_xhtml': 'xhtml' in publish_options
        }

    def save_settings(self, request):
        opts = []
        for _opt in self.OPTIONS:
            if self.cleaned_data.get('publish_{0}'.format(_opt)):
                opts.append(_opt)

        config.set_configuration('PUBLISH_OPTIONS', opts)

        try:
            config.save_configuration()
        except config.ConfigurationError as err:
            raise err


class PublishingDefaultsForm(BaseControlForm, forms.Form):
    book_css = forms.CharField(
        label=_('Book CSS'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 30,
            'style': 'max-width: 500px'
        })
    )
    ebook_css = forms.CharField(
        label=_('E-Book CSS'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 30,
            'style': 'max-width: 500px'
        })
    )
    pdf_css = forms.CharField(
        label=_('PDF CSS'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 30,
            'style': 'max-width: 500px'
        })
    )
    odt_css = forms.CharField(
        label=_('ODT CSS'),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 30,
            'style': 'max-width: 500px'
        })
    )

    @classmethod
    def initial_data(cls):
        return {
            'book_css': config.get_configuration('BOOKTYPE_CSS_BOOK', ''),
            'ebook_css': config.get_configuration('BOOKTYPE_CSS_EBOOK', ''),
            'pdf_css': config.get_configuration('BOOKTYPE_CSS_PDF', ''),
            'odt_css': config.get_configuration('BOOKTYPE_CSS_ODT', '')
        }

    def save_settings(self, request):
        data = self.__class__.initial_data()

        if self.cleaned_data['book_css'] != data['book_css']:
            config.set_configuration(
                'BOOKTYPE_CSS_BOOK', self.cleaned_data['book_css'])

        if self.cleaned_data['ebook_css'] != data['ebook_css']:
            config.set_configuration(
                'BOOKTYPE_CSS_EBOOK', self.cleaned_data['ebook_css'])

        if self.cleaned_data['pdf_css'] != data['pdf_css']:
            config.set_configuration(
                'BOOKTYPE_CSS_PDF', self.cleaned_data['pdf_css'])

        if self.cleaned_data['odt_css'] != data['odt_css']:
            config.set_configuration(
                'BOOKTYPE_CSS_ODT', self.cleaned_data['odt_css'])

        try:
            config.save_configuration()
        except config.ConfigurationError as err:
            raise err


class ListOfGroupsForm(BaseControlForm, forms.Form):
    pass

    @classmethod
    def extra_context(cls):
        return {
            'groups': BookiGroup.objects.all().order_by("name")
        }


class AddGroupForm(BaseControlForm, GroupCreateForm, forms.ModelForm):

    success_message = _('Successfully created new group.')

    class Meta:
        model = BookiGroup
        fields = [
            'name', 'description', 'owner'
        ]

    def save_settings(self, request):
        group = self.save(commit=False)
        group.url_name = misc.booktype_slugify(group.name)
        group.created = timezone.now()
        group.save()

        # auto-join owner as team member
        group.members.add(request.user)

        # set group image if exists in post data
        group_image = self.files.get('group_image', None)
        if group_image:
            self.set_group_image(group.pk, group_image)

        return group


class ListOfRolesForm(BaseControlForm, forms.Form):
    pass

    @classmethod
    def extra_context(cls):
        return {
            'roles': Role.objects.all().order_by("name")
        }


class AddRoleForm(BaseControlForm, forms.ModelForm):

    success_message = _('Successfully created new role.')
    success_url = '#list-of-roles'

    class Meta:
        model = Role
        exclude = ['members']
        widgets = {
            'description': forms.Textarea,
            'permissions': GroupedCheckboxSelectMultiple(
                choices=Permission.objects.all(),
                attrs={
                    'group_by': 'app_name',
                    'css_class': 'grouped_perms'
                }
            ),
        }

    def get_cancel_url(self):
        return "{0}{1}".format(self.cancel_url, self.success_url)

    def save_settings(self, request):
        role = self.save()
        return role


class DefaultRolesForm(BaseControlForm, forms.Form):
    ROLES_CHOICES = \
        [('__no_role__', _('None'))] + \
        [(r.name, r.name) for r in Role.objects.all()]
    anonymous = 'anonymous_users'
    registered = 'registered_users'

    anonymous_users = forms.ChoiceField(
        choices=ROLES_CHOICES, required=False,
        label=_('Role for anonymous users')
    )
    registered_users = forms.ChoiceField(
        choices=ROLES_CHOICES, required=False,
        label=_('Role for registered users')
    )

    @classmethod
    def initial_data(cls):
        return {
            cls.anonymous: config.get_configuration(
                'DEFAULT_ROLE_%s' % cls.anonymous,
                cls.anonymous
            ),
            cls.registered: config.get_configuration(
                'DEFAULT_ROLE_%s' % cls.registered,
                cls.registered
            )
        }

    def save_settings(self, request):
        config.set_configuration(
            'DEFAULT_ROLE_%s' % self.anonymous,
            self.cleaned_data[self.anonymous]
        )
        config.set_configuration(
            'DEFAULT_ROLE_%s' % self.registered,
            self.cleaned_data[self.registered]
        )

        try:
            config.save_configuration()
        except config.ConfigurationError as err:
            raise err
