from django.forms import widgets

class BaseBooktypeForm(object):
    '''
    Generic class to add form-control class to all fields
    in a form
    '''

    def __init__(self, *args, **kwargs):
        super(BaseBooktypeForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            css_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = '%s form-control' % css_class