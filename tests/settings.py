import os
import django
from unipath import Path

BASE_DIR = Path(os.path.abspath(__file__))

BOOKTYPE_SITE_NAME = ''
BOOKTYPE_SITE_DIR = 'tests'
THIS_BOOKTYPE_SERVER = ''
BOOKTYPE_URL = ''

BOOKTYPE_ROOT = BASE_DIR.parent

STATIC_ROOT = BASE_DIR.parent.child("static")
STATIC_URL = '{}/static/'.format(BOOKTYPE_URL)

DATA_ROOT = BASE_DIR.parent.child("data")
DATA_URL = '{}/data/'.format(BOOKTYPE_URL)

MEDIA_ROOT = DATA_ROOT
MEDIA_URL = DATA_URL

# DEBUG
DEBUG = TEMPLATE_DEBUG = True

# PROFILE
PROFILE_ACTIVE = 'test'

if django.VERSION[:2] < (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'
    TEST_DISCOVER_TOP_LEVEL = BASE_DIR.parent.parent.child('lib')
    TEST_DISCOVER_PATTERN = 'test*.py'

ROOT_URLCONF = 'urls'

SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

SECRET_KEY = 'enc*ln*vp^o2p1p6of8ip9v5_tt6r#fh2-!-@pl0ur^6ul6e)l'
COVER_IMAGE_UPLOAD_DIR = 'cover_images/'
PROFILE_IMAGE_UPLOAD_DIR = 'profile_images/'


# E-MAIL
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CACHES
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': ''
    }
}

# REDIS
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'booktype.apps.core.middleware.SecurityMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_celery_results',

    # list of booki apps
    'booki.editor',

    'booktypecontrol',

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

    'booki.messaging',

    'sputnik',
)

if django.VERSION[:2] < (1, 6):
    INSTALLED_APPS += ('discover_runner', )

if django.VERSION[:2] < (1, 7):
    INSTALLED_APPS += ('south', )

# this is for pep8
standard_format = {
    'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
    'datefmt': "%d/%b/%Y %H:%M:%S"
}

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': standard_format,
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
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
# from booki.utils import config
#
# try:
#    BOOKTYPE_CONFIG = config.loadConfiguration()
# except config.ConfigurationError:
#    BOOKTYPE_CONFIG = {}

BOOKTYPE_NAME = BOOKTYPE_SITE_NAME
BOOKI_NAME = BOOKTYPE_NAME
BOOKI_ROOT = BOOKTYPE_ROOT
BOOKI_URL = BOOKTYPE_URL
THIS_BOOKI_SERVER = THIS_BOOKTYPE_SERVER
BOOKI_MAINTENANCE_MODE = False
