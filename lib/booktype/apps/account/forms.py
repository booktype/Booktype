from django.core.validators import validate_email
from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm

from booki.editor.models import BookHistory
from booktype.apps.core.models import Book, Role
from booktype.apps.core.forms import BaseBooktypeForm
from booktype.apps.portal.widgets import RemovableImageWidget


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
        queryset=Role.objects.exclude(Q(name='anonymous_users') | Q(name='registered_users')),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def clean_email_list(self):
        email_list_string = self.cleaned_data['email_list']
        email_list = [email.strip() for email in email_list_string.split(',')]

        for email in email_list:
            validate_email(email)

        return email_list

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
