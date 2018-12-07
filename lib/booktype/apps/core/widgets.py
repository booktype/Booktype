# -*- coding: utf-8 -*-

from django import forms
from django.forms.widgets import CheckboxInput
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.html import format_html


class GroupedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Widget for grouping checkboxes with a given group_by field
    """

    def __init__(self, attrs={}, choices=()):
        """
        Widget constructor.

        Args:
            - choices: Django queryset
            - attrs: Inherit argument from parent class. If you pass a group_by
                key, it will used to order the queryset. group_by should be an
                attribute of the each element in the queryset.
        """

        super(GroupedCheckboxSelectMultiple, self).__init__(attrs, choices)

        self.group_by = attrs.get('group_by', None)
        self.css_class = attrs.pop('css_class', '')

        grouped_query = {}
        for obj in choices.order_by(self.group_by):
            order_field = getattr(obj, self.group_by)
            grouped_query.setdefault(order_field, []).append(obj)

        self.grouped = grouped_query

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []

        has_id = attrs and 'id' in attrs
        attrs.update({u'name':name})
        final_attrs = self.build_attrs(attrs)

        grouped_list = []
        for order_key, elems in self.grouped.items():
            fieldset = '<fieldset class="%s"><legend>%s</legend><ul>' \
                % (self.css_class, order_key.title())
            output = [fieldset]

            # Normalize to strings
            str_values = set([force_text(v) for v in value])

            for i, obj in enumerate(elems):
                option_value, option_label = obj.pk, obj.__unicode__()
                # If an ID attribute was given, add a numeric index as a suffix
                # so that the checkboxes don't all have the same ID attribute.
                if has_id:
                    final_attrs = dict(
                        final_attrs,
                        id='%s_%s_%s' % (attrs['id'], i, order_key)
                    )
                    label_for = format_html(' for="{0}"', final_attrs['id'])
                else:
                    label_for = ''

                cb = CheckboxInput(
                    final_attrs, check_test=lambda value: value in str_values)
                option_value = force_text(option_value)
                rendered_cb = cb.render(name, option_value)
                option_label = force_text(option_label)
                output.append(
                    format_html('<li><label{0}>{1} {2}</label></li>',
                                label_for, rendered_cb, option_label)
                )
            output.append('</ul></fieldset>')
            grouped_list.append('\n'.join(output))

        return mark_safe('\n'.join(grouped_list))
