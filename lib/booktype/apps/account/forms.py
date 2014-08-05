from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm

from booktype.apps.core.forms import BaseBooktypeForm
from booktype.apps.portal.widgets import RemovableImageWidget

class UserSettingsForm(BaseBooktypeForm, forms.ModelForm):
    email = forms.EmailField(label=_('Email'))
    first_name = forms.CharField(label=_('Full name'))

    # profile fields
    aboutyourself = forms.CharField(
        label=_('About yourself'),
        widget=forms.Textarea(attrs={'rows': '20', 'cols': '40'})
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