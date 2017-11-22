import logging

from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm

from booktype.utils import config
from booki.editor.models import BookHistory, Language, License, METADATA_FIELDS
from booktype.apps.core.models import Book, Role, BookSkeleton
from booktype.apps.core.forms import BaseBooktypeForm
from booktype.apps.portal.widgets import RemovableImageWidget


logger = logging.getLogger('booktype.apps.account.forms')


class UserSettingsForm(BaseBooktypeForm, forms.ModelForm):
    email = forms.EmailField(label=_('Email'))
    first_name = forms.CharField(
        label=_('Full name'),
        required=False
    )

    # profile fields
    aboutyourself = forms.CharField(
        label=_('About yourself'),
        widget=forms.Textarea(attrs={'rows': '20', 'cols': '40'}),
        required=False
    )
    profile_pic = forms.FileField(
        label=_('Profile image'),
        required=False,
        widget=RemovableImageWidget(attrs={
            'label_class': 'checkbox-inline',
            'input_class': 'group-image-removable'
        })
    )
    notification = forms.CharField(
        label=_('Notification filter'),
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'first_name']


class UserPasswordChangeForm(BaseBooktypeForm, PasswordChangeForm):
    new_password2 = forms.CharField(
        label=_('Password (again)'),
        widget=forms.PasswordInput
    )


class UserInviteForm(BaseBooktypeForm, forms.Form):
    email_list = forms.CharField(
        label=_('Enter email addresses separated by comma'),
        widget=forms.Textarea
    )
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea
    )
    books = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(UserInviteForm, self).__init__(*args, **kwargs)

        # books that the user can invite to collaborate in
        book_ids = BookHistory.objects.filter(user=user).values_list(
            'book', flat=True).distinct()

        b_query = Book.objects.all()
        if not user.is_superuser:
            b_query = b_query.filter(Q(id__in=book_ids) | Q(owner=user))

        self.fields['books'].queryset = b_query.order_by('title')

        # query roles
        roles_qs = Role.objects.exclude(Q(name='anonymous_users') | Q(name='registered_users'))
        self.fields['roles'].queryset = roles_qs

    def clean_email_list(self):
        email_list_string = self.cleaned_data['email_list']
        email_list = [email.strip() for email in email_list_string.split(',')]

        for email in email_list:
            validate_email(email)

        return email_list


def _make_choices(queryset):
    """
    Language and License share field names: abbreviation and name.
    Taking advantage ot this to create one single dummy method
    """
    choices = []
    for obj in queryset:
        choices.append((obj.abbrevation, obj.name))
    return choices


def _languages_choices():
    return _make_choices(queryset=Language.objects.all())


def _licenses_choices():
    return _make_choices(queryset=License.objects.all().order_by('name'))


class BookCreationForm(BaseBooktypeForm, forms.Form):
    # STEP 1: Book information
    title = forms.CharField(
        label=_("Working title"),
        max_length=200, required=True)

    # author = forms.CharField(
    #     label=_("Author"), max_length=200)

    language = forms.ChoiceField(
        label=_("Language of the book"), choices=_languages_choices)

    license = forms.ChoiceField(
        label=_("License"), choices=_licenses_choices)

    visible_to_everyone = forms.BooleanField(
        label=_("Visible to everyone"),
        help_text=_("BE AWARE: If you tick this box ALL users on the system can see or read the book. "
                    "(It is not necessary to tick the box to invite people to read or collaborate into the book. "
                    "To invite people, please use the function on your dashboard or the info page of this book)."))

    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'cols': 20, 'rows': 3}),
        help_text=_("Optional: describe the book to other users on this platform"))

    # -------- END STEP 1 -------------

    # STEP 2: Metadata
    # NOTE: fields created on the fly, see __init__ method

    # STEP 3: Creation mode
    # NOTE: creation_mode field created in template since we need tooltips. Will be this way until
    # we create our custom label renderer with tooltip icon

    base_book = forms.ModelChoiceField(
        label=_("Select the base book"),
        queryset=Book.objects.none())

    base_skeleton = forms.ModelChoiceField(
        label=_("Select the skeleton"),
        queryset=BookSkeleton.objects.all(),
        required=False)

    # based_on_file created in template since it needs drag area

    # -------- END STEP 3 -------------

    # STEP 4: Cover image
    cover_image = forms.ImageField(
        label=_("Cover Image"),
        required=True)

    cover_title = forms.CharField(
        label=_("Title of cover"), required=True)

    cover_creator = forms.CharField(
        label=_("Creator of cover"), required=False)

    cover_license = forms.ChoiceField(
        label=_("License"), choices=_licenses_choices)

    # -------- END STEP 4 -------------

    def __init__(self, base_book_qs=None, *args, **kwargs):
        super(BookCreationForm, self).__init__(*args, **kwargs)

        # time to build metadata fields
        self.metadata_fields = config.get_configuration('CREATE_BOOK_METADATA', [])

        # TODO: extract this to a separate method to use it also in booktype.apps.edit.forms.MetadataForm
        for field, label, standard in METADATA_FIELDS:
            field_name = '%s.%s' % (standard, field)
            if field_name not in self.metadata_fields:
                continue

            self.fields[field_name] = forms.CharField(
                label=label, required=False)

            c_field = self.fields[field_name]
            BaseBooktypeForm.apply_class(c_field, 'form-control')

            # apply widgets if needed
            if field in self.Meta.widgets:
                c_field.widget = self.Meta.widgets[field]

        if base_book_qs is not None:
            self.fields['base_book'].queryset = base_book_qs
        else:
            logger.warn("base_book_qs queryset parameter was not provided. Using empty queryset")

    class Meta:
        text_area = forms.Textarea(attrs={'class': 'form-control', 'cols': 20, 'rows': 3})
        widgets = {
            'short_description': text_area,
            'long_description': text_area
        }

    def get_metadata_fields(self):
        """
        Retrieve the fields related to metadata information
        """
        for mfield in self.metadata_fields:
            field = self.fields[mfield]
            yield field.get_bound_field(self, mfield)
