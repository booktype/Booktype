# -*- coding: utf-8 -*-
from django import forms
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _


class BkFileWidget(forms.FileInput):
    """
    A FileField Widget that shows its current value if it has one.
    Only reason to have this custom widget it's because we have custom
    html structure for forms
    """

    def __init__(self, attrs={}):
        super(BkFileWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append(
                '%s <a target="_blank" href="%s">%s</a> <br /><label></label>' % (
                    _('Currently:'), value.url, value))

        output.append(super(BkFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))
