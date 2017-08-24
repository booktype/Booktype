from django.template.loaders.base import Loader

import os

from django.conf import settings
from django.template import TemplateDoesNotExist
from django.utils._os import safe_join


class Loader(Loader):
    """Load for templates connected with themes.

    Themes are located in $INSTANCE/themes directory. Inside that directory users can create
    subdirectory "templates" where they will put their template files. The full path to such
    template file will be themes/$THEME_NAME/$TEMPLATE_NAME, while on the disk it would be
    $INSTANCE/themes/$THEME_NAME/templates/$TEMPLATE_NAME.
    """

    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        if not template_dirs:
            template_dirs = []

            if template_name.startswith('themes/'):
                splts = template_name.split('/')

                if len(splts) > 2:
                    theme_dir = '{}/themes/{}/templates/'.format(settings.BOOKTYPE_ROOT, splts[1])
                    if os.path.isdir(theme_dir):
                        template_dirs = [theme_dir]

        for template_dir in template_dirs:
            try:
                splts = template_name.split('/')
                # we have already checked the length of the splts
                yield safe_join(template_dir, splts[2])
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of template_dir.
                pass

    def load_template_source(self, template_name, template_dirs=None):
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return (fp.read().decode(settings.FILE_CHARSET), filepath)
            except IOError:
                pass
        raise TemplateDoesNotExist(template_name)
