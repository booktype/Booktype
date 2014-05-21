from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm

class BaseAccountsForm(object):
    '''
    Generic class to add form-control class to all fields
    in a form
    '''

    def __init__(self, *args, **kwargs):
        super(BaseAccountsForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            css_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = '%s form-control' % css_class


class UserSettingsForm(BaseAccountsForm, forms.ModelForm):
    email = forms.EmailField(label=_('Email'))
    first_name = forms.CharField(label=_('Full name'))

    # profile fields
    aboutyourself = forms.CharField(
        label=_('About yourself'),
        widget=forms.Textarea(attrs={'rows': '20', 'cols': '40'})
    )
    profile_pic = forms.FileField(
        label=_('Profile image'), 
        required=False
    )
    notification = forms.CharField(
        label=_('Notification filter'), 
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'first_name']

class UserPasswordChangeForm(BaseAccountsForm, PasswordChangeForm):
    new_password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput
    )