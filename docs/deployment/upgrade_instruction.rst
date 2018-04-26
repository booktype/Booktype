====================
Upgrade instructions
====================



Booktype 1.6.1
--------------

Templates have been changed a bit in this release. Check lib/booki/editor/templates/editor/
directory. Structure has been changed for:

* edit_book.html
* edit_header.html
* edit_sidebar.html
* edit_content.html
* edit_templates.html
* tab_chapters.html
* tab_history.html
* tab_notes.html
* tab_publish.html
* tab_settings.html
* tab_version.html


Booktype 1.6.0
--------------

There are changes in the database schema and database migration is required.


Booktype 1.5.5
--------------

There are changes in the database schema and database migration is required.

Update your project settings.py file. If you are using default settings for
Objavi you should update them::

    OBJAVI_URL = "http://objavi.booktype.pro/"
    ESPRI_URL = "http://objavi.booktype.pro/espri"


Booktype 1.5.4
--------------    

There are changes in the database schema and database migration is required.


Booktype 1.5.3
--------------

Update your project settings.py file to use messaging framework. You have to::

    - Add new options

       MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage' 
       TEMPLATE_CONTEXT_PROCESSORS = ('django.contrib.auth.context_processors.auth', 
                                      'django.contrib.messages.context_processors.messages') 

    - Add new messaging middleware to the list:
       MIDDLEWARE_CLASSES = (...,
                             'django.contrib.messages.middleware.MessageMiddleware',
                             ...)

    - Add new Django app to the list:
       INSTALLED_APPS = (...,
                         'django.contrib.messages', 
                         ...)

Notice: All of these changes will require "django-admin migrate" at the end.

Upgrade your config files to include Control Center::

    - Upgrade settings.py file with:
      INSTALLED_APPS = (...,
                        'booktypecontrol'
                        ,...)


    - Add to the end of settings.py file

      from booki.utils import config

      try:
        BOOKTYPE_CONFIG = config.loadConfiguration()
      except config.ConfigurationError:
        BOOKTYPE_CONFIG = {}

    - Template file lib/booki/portal/templates/base.html has been modified. 

Notice: All of these changes will require "django-admin migrate" at the end.

Style of database configuration has been changed so please update your configuration. This is a normal 
Django database configuration and please check Django documentation for more information and options.

It used to be::

    DATABASE_ENGINE = 'postgresql_psycopg2'
    DATABASE_NAME = '' 
    DATABASE_USER = '' 
    DATABASE_PASSWORD = '' 
    DATABASE_HOST = 'localhost'
    DATABASE_PORT = ''

Now it is::

    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql_psycopg2', 
                          'NAME': '', 
                          'USER': '', 
                          'PASSWORD': '', 
                          'HOST': 'localhost', 
                          'PORT': '' 
                          } 
               }

New configuration for load Django templates. Please change your configuration::

    import django

    if django.VERSION[1] < 3:
        TEMPLATE_LOADERS = (
                            'django.template.loaders.filesystem.load_template_source',
                            'django.template.loaders.app_directories.load_template_source',
                            'django.template.loaders.eggs.load_template_source',
                           )
    else:
        TEMPLATE_LOADERS = (
                            'django.template.loaders.filesystem.Loader',
                            'django.template.loaders.app_directories.Loader',
                            'django.template.loaders.eggs.Loader',
                           )
    
Booktype 1.5.2
--------------

Update your project settings.py. You have to add new middleware called "LocaleMiddleware" to the list.::

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.middleware.transaction.TransactionMiddleware'
    )    

Update your project settings.py. You don't have to but you can comment LANGUAGES options.::

    LANGUAGE_CODE = 'en-us'

    # Uncomment this if you want to limit language translations only to specific list of languages
    #
    # gettext = lambda s: s
    #
    # LANGUAGES = (
    #  ('en-us', gettext('English'))
    # )

By default "createbooktype" script will now create "locale" directory in your Booktype project.

Update your project settings.py::

    LOCALE_PATHS = (
         '%s/locale' % os.path.dirname(booki.__file__),
    )

