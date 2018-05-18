# Django settings for docs project.
# import source code dir
import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), os.pardir))

SITE_ID = 303
DEBUG = True
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = 'enc*ln*vp^o2p1p6of8ip9v5_tt6r#fh2-!-@pl0ur^6ul6e)l'

COVER_IMAGE_UPLOAD_DIR = 'cover_images/'

PROFILE_IMAGE_UPLOAD_DIR ='profile_images/'

BOOKTYPE_URL = 'http://booktype.example.com/'

STATIC_URL = '{}static/'.format(BOOKTYPE_URL)

COMPRESS_URL = STATIC_URL

DATABASES = {"default": {
    "NAME": ":memory:",
    "ENGINE": "django.db.backends.sqlite3",
    "USER": '',
    "PASSWORD": '',
    "PORT": '',
}}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_celery_results',
    'compressor',

    # list of booki apps
    'booki.editor',

    # needed for translation engine
    'booktype',

    # list of booktype apps
    'booktype.apps.core',
    'booktype.apps.portal',
    'booktype.apps.loadsave',
    'booktype.apps.importer',
    'booktype.apps.convert',
    'booktype.apps.edit',
    'booktype.apps.reader',
    'booktype.apps.account',
    'booktype.apps.themes',
    'booktype.apps.export',

    # to be removed
    'booki.messaging',

    'sputnik',
    'booktypecontrol'
)
