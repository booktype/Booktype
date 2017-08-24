from django import forms
from django.utils.html import escape
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from booktype.utils.misc import booktype_slugify
from booki.editor.models import BookiGroup

from booktype.utils import misc
from booktype.apps.core.forms import BaseBooktypeForm

from widgets import RemovableImageWidget


class SpanErrorList(ErrorList):
    def __unicode__(self):
        return unicode(self.as_spans())

    def as_spans(self):
        return "<span style='color: red'>%s</span>" % (
            ",".join([e for e in self]))


class BaseGroupForm(BaseBooktypeForm, forms.ModelForm):
    name = forms.CharField()
    description = forms.CharField(
        label=_('Description (250 characters)'),
        required=False,
        max_length=250,
        widget=forms.Textarea(attrs={'rows': '10', 'cols': '40'})
    )
    group_image = forms.FileField(
        label=_('Group image'),
        required=False,
        widget=RemovableImageWidget(attrs={
                'label_class': 'checkbox-inline',
                'input_class': 'group-image-removable'
            }
        )
    )

    class Meta:
        model = BookiGroup
        fields = [
            'name', 'description'
        ]

    def __init__(self, *args, **kwargs):
        kwargs.update({'error_class': SpanErrorList})
        super(BaseGroupForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        new_url_name = booktype_slugify(self.cleaned_data['name'])
        group_data_url_name = BookiGroup.objects.filter(url_name=new_url_name).exclude(pk=self.instance.pk)

        if len(group_data_url_name) > 0:
            raise ValidationError(_('Group name is already in use'))

        return self.cleaned_data.get('name', '')

    def clean_description(self):
        return escape(self.cleaned_data.get('description', ''))

    def set_group_image(self, group_id, group_image):
        try:
            filename = misc.set_group_image(group_id, group_image, 240, 240)

            if len(filename) == 0:
                raise ValidationError(_('Only JPEG file is allowed for group image.'))
            else:
                misc.set_group_image("{}_small".format(group_id), group_image, 18, 18)
        except Exception as err:
            # TODO: we should do something here
            print err


class GroupCreateForm(BaseGroupForm):
    pass


class GroupUpdateForm(BaseGroupForm):

    def clean_group_image(self):
        group_image = self.files.get('group_image', None)
        group_id = str(self.instance.pk)

        if group_image:
            self.set_group_image(group_id, group_image)
        return group_image
