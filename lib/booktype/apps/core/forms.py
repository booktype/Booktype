# -*- coding: utf-8 -*-


class BaseBooktypeForm(object):
    '''
    Generic class to add form-control class to all fields
    in a form
    '''

    skip_select_and_checkbox = False

    @classmethod
    def apply_class(cls, field, css_class):
        field.widget.attrs['class'] = '%s form-control' % css_class

    def __init__(self, *args, **kwargs):
        super(BaseBooktypeForm, self).__init__(*args, **kwargs)

        _apply_class = BaseBooktypeForm.apply_class

        for field in self.fields.values():
            css_class = field.widget.attrs.get('class', '')

            if field.widget.__class__.__name__ in ['Select', 'Checkbox']:
                if not self.skip_select_and_checkbox:
                    _apply_class(field, css_class)
            else:
                _apply_class(field, css_class)
