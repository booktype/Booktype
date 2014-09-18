import os
import django
from unipath import Path

BASE_DIR = Path(os.path.abspath(__file__))

# PROFILE
PROFILE_ACTIVE = 'test'

if django.VERSION[:2] < (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'
    TEST_DISCOVER_TOP_LEVEL = BASE_DIR.parent.parent.child('lib')
    TEST_DISCOVER_PATTERN = 'seltest*.py'

SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

# BOOKTYPE
BOOKTYPE_SITE_NAME = 'Booktype site'
BOOKTYPE_SITE_DIR = 'tests'
THIS_BOOKTYPE_SERVER = ''

BOOKTYPE_ROOT = Path(os.path.abspath(__file__)).ancestor(3)

BOOKTYPE_URL = ''

# E-MAIL OPTIONS
REPORT_EMAIL_USER = 'booktype@booktype.pro'

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# site_static
import booki

# static
STATIC_ROOT = BOOKTYPE_ROOT.child('static')
STATIC_URL = '{}/static/'.format(BOOKTYPE_URL)

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    BOOKTYPE_ROOT.child(BOOKTYPE_SITE_NAME).child('static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder'
)

# data
DATA_ROOT = BOOKTYPE_ROOT.child('data')
DATA_URL = '{}/data/'.format(BOOKTYPE_URL)

# profile images
PROFILE_IMAGE_UPLOAD_DIR = 'profile_images/'

# If you don't want to use default profile image you can set your own.
# Place the image inside of /static/images/ directory in your Booktype project directory.
# DEFAULT_PROFILE_IMAGE='anonymous.png'

# book cover images
COVER_IMAGE_UPLOAD_DIR = 'cover_images/'


SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

LOCALE_PATHS = (
    BOOKTYPE_ROOT.child(BOOKTYPE_SITE_NAME).child('locale'),
    Path(booki.__file__).parent.child('locale'),
    Path(booki.__file__).parent.child('booktype').child('locale')
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'enc*ln*vp^o2p1p6of8ip9v5_tt6r#fh2-!-@pl0ur^6ul6e)l'

# Storage for messages framework
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# List of callables that know how to import templates from various sources.

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.csrf"
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)


# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '{}.wsgi.application'.format('mybook_site')

TEMPLATE_DIRS = (
    BOOKTYPE_ROOT.child(BOOKTYPE_SITE_NAME).child('templates'),
    Path(booki.__file__).parent.child('templates')
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'south',
    'compressor',
    'djcelery',

    # list of booki apps
    'booki.editor',

    # list of booktype apps
    'booktype.apps.core',
    'booktype.apps.portal',
    'booktype.apps.loadsave',
    'booktype.apps.importer',
    'booktype.apps.convert',
    'booktype.apps.edit',
    'booktype.apps.account',

    # to be removed
    'booki.messaging',

    'sputnik',
    'booktypecontrol'
)

BOOKTYPE_CONVERTER_MODULES = (
    'booktype.convert.converters',
)

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

# DEPRECATED CONFIG

BOOKTYPE_NAME = BOOKTYPE_SITE_NAME
BOOKI_NAME = BOOKTYPE_NAME
BOOKI_ROOT = BOOKTYPE_ROOT
BOOKI_URL = BOOKTYPE_URL
THIS_BOOKI_SERVER = THIS_BOOKTYPE_SERVER
BOOKI_MAINTENANCE_MODE = False

# WEB SITE URL

THIS_BOOKTYPE_SERVER = ''
BOOKTYPE_URL = ''
# BOOKTYPE_URL = 'http://{}'.format(THIS_BOOKTYPE_SERVER)

STATIC_URL = '{}/static/'.format(BOOKTYPE_URL)
DATA_URL = '{}/data/'.format(BOOKTYPE_URL)
MEDIA_URL = DATA_URL

# DEBUGGING
DEBUG = TEMPLATE_DEBUG = True

# COMPRESSION
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# PROFILE

# URL ROUTER
ROOT_URLCONF = 'urls'

# DATABASE
DATABASES = {
    'default':
    {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': ''
    }
}

# E-MAIL
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CACHE
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.db.backends': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': True,
        },
        'booktype': {
            'handlers': ['null'],
            'level': 'INFO'
        }
    }
}


# READ CONFIGURAION
from booktype.utils import config

try:
    BOOKTYPE_CONFIG = config.load_configuration()
except config.ConfigurationError:
    BOOKTYPE_CONFIG = {}