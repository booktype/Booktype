import os
import shutil

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _

from booktype.apps.core.forms import BaseBooktypeForm
from booki.utils import config, misc

class BaseControlForm(BaseBooktypeForm):

    def save_settings(self):
        pass

class SiteDescriptionForm(BaseControlForm, forms.Form):
    title = forms.CharField(
            label=_("Site title"),
            required=True, 
            error_messages={'required': _('Site title is required.')},
            max_length=200
        )
    tagline = forms.CharField(
            label=_("Tagline"), 
            required=False,
            max_length=200
        )
    favicon = forms.FileField(
            label=_("Favicon"), 
            required=False, 
            help_text=_("Upload .ico file")
        )

    def save_settings(self):
        config.setConfiguration('BOOKTYPE_SITE_NAME', self.cleaned_data['title'])
        config.setConfiguration('BOOKTYPE_SITE_TAGLINE', self.cleaned_data['tagline'])

        if self.files.has_key('favicon'):
            # just check for any kind of silly error
            try:
                fh, fname = misc.saveUploadedAsFile(self.files['favicon'])
                shutil.move(fname, '%s/favicon.ico' % settings.STATIC_ROOT)

                config.setConfiguration('BOOKTYPE_SITE_FAVICON', '%s/static/favicon.ico' % settings.BOOKTYPE_URL)
            except:
                pass

        try:
            config.saveConfiguration()
        except config.ConfigurationError as err:
            raise err


class AppearanceForm(BaseControlForm, forms.Form):
    css = forms.CharField(
            label=_('CSS'),
            required=False,
            widget=forms.Textarea(attrs={'rows': 20, 'cols': 40})
        )

    def save_settings(self):
        try:
            # should really save it in a safe way
            f = open('%s/css/_user.css' % settings.STATIC_ROOT, 'w')
            f.write(self.cleaned_data['css'].encode('utf8'))
            f.close()
        except IOError as err:
            raise err


class FrontpageForm(BaseControlForm, forms.Form):
    description = forms.CharField(
            label=_('Welcome message'),
            required=False, 
            widget=forms.Textarea(attrs={'rows': 20, 'cols': 40})
        )
    show_changes = forms.BooleanField(
            label=_('Show activity'), 
            required=False
        )

    def save_settings(self):
        staticRoot = settings.BOOKTYPE_ROOT
        config.setConfiguration('BOOKTYPE_FRONTPAGE_HISTORY', self.cleaned_data['show_changes'])

        if not os.path.exists('%s/templates/portal/' % staticRoot):
            os.makedirs('%s/templates/portal/' % staticRoot)

        try:
            f = open('%s/templates/portal/welcome_message.html' % staticRoot, 'w')
            
            text_data = self.cleaned_data.get('description', '')
            text_data = text_data.replace('{%', '').replace('%}', '').replace('{{', '').replace('}}', '')

            f.write(text_data.encode('utf8'))
            f.close()
            config.saveConfiguration()

        except IOError as err:
            raise err
        except config.ConfigurationError as err:
            raise err