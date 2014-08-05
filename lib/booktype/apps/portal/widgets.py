from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

class RemovableImageWidget(CheckboxInput):

    def __init__(self, *args, **kwargs):
        self.attrs = kwargs.get('attrs', {})
        super(RemovableImageWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs={}):
        value = value
        attrs.update(self.attrs)
        _template = '%(image_tag)s %(fileinput)s<br/><label></label><label class="%(label_class)s">%(checkbox_input)s%(label_text)s</label>'
        
        # prepare file input css class
        label_class = attrs.pop('label_class', '')
        fileinput_attrs = {}
        fileinput_attrs.update(attrs)
        fileinput_attrs['class'] = '%s %s' % (attrs.pop('input_class'), attrs.get('class', ''))

        if value:
            fileinput = ClearableFileInput().render(name, value, fileinput_attrs)
            checkbox_input = CheckboxInput().render('%s_remove' % name, False, attrs={'class': ''})
            content = _template % {
                'image_tag': '<img src="%s" width="50">' % value,
                'fileinput': fileinput,
                'checkbox_input': checkbox_input,
                'label_class': label_class,
                'label_text': _('Remove')
            }
            return mark_safe(content)
        else:
            return ClearableFileInput().render(name, value, attrs)