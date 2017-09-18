from django import forms
from booki.editor.models import Book
from django.utils.translation import ugettext_lazy as _

from booktype.apps.core.forms import BaseBooktypeForm

class EditBookInfoForm(BaseBooktypeForm, forms.ModelForm):

    description = forms.CharField(
            label=_("Book description"),
            required=False,
            widget=forms.Textarea(attrs={'style': "width: 100%; height: 210px;"})
        )
    book_cover = forms.ImageField(
            label=_("Book image"),
            required=False
        )
    hidden = forms.BooleanField(
            label=_('Hide this book from other people'),
            required=False
        )

    class Meta:
        model = Book
        exclude = [
            'url_title', 'title',
            'status', 'language',
            'version', 'group',
            'created', 'published',
            'permission', 'cover'
        ]

        fields = [
            'description', 'book_cover',
            'owner', 'license', 'hidden'
        ]

    def __init__(self, user, *args, **kwargs):
        super(EditBookInfoForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            del self.fields['owner']
        else:
            self.fields['owner'].queryset = self.fields['owner'].queryset.order_by('username')

