=================
Booktype settings
=================

.. contents::
   :local:
   :depth: 1


.. warning::
   
   Work in progress.   


Booktype specific
=================

.. setting:: BOOKTYPE_SITE_NAME

BOOKTYPE_SITE_NAME
-------------------

You can name your Booktype instance. This name will be used in default templates as the name of your site.

Example::
    
    BOOKTYPE_SITE_NAME = 'My Booktype instance'


.. setting:: BOOKTYPE_SITE_DIR

BOOKTYPE_SITE_DIR
-----------------

This is the directory name of your Booktype project on disk. It always ends with "_site".

Example::

    BOOKTYPE_SITE_DIR = 'test_site'

.. note::

    Createbooktype script will configure this value appropriately. User will need to change this value only when changing or renaming Booktype project layout on disk.


.. setting:: BOOKTYPE_ROOT

BOOKTYPE_ROOT
-------------

Full path pointing to location of Booktype project.

Example::

    BOOKTYPE_ROOT = '/var/www/mybooktype'

.. note::

    Createbooktype script will configure this value appropriately. User will need to change this value only when changing location of Booktype project.


.. setting:: BOOKTYPE_URL

BOOKTYPE_URL
------------

URL pointing to your Booktype project.

Example::

    BOOKTYPE_URL = 'http://booktype.mydomain.com'

.. note::

    Other URL settings will be configured using this value as a base URL.


.. setting:: PROFILE_ACTIVE

PROFILE_ACTIVE
--------------

Each Booktype instance has more then one profile. Profiles are used so we can have different settings and environment for our Booktype
instance in production mode, development mode or staging mode. Different profiles have different settings file and this value is
configured accordingly in setting file.


Example for development profile::

    PROFILE_ACTIVE = 'dev'

.. note::

    There is no need for user to change this settings unless new profile is being created.


.. setting:: DATA_ROOT

DATA_ROOT
---------

Full path where user uploaded data is. Default value is using :setting:`BOOKTYPE_ROOT` to generate this settings.

.. note::

    Change this only if user data is not at the same location as Booktype project.


.. setting:: DATA_URL

DATA_URL
--------

Full URL where user uploaded data is. Default value is using :setting:`BOOKTYPE_URL` to generate this settings.

.. note::

    Change this only if user data is not at the same URL as Booktype project.


.. setting:: COVER_IMAGE_UPLOAD_DIR

COVER_IMAGE_UPLOAD_DIR
----------------------

Default: ``"cover_images/"``. 

Name of the directory where cover images are placed. Base directory is :setting:`DATA_ROOT`.


.. setting:: PROFILE_IMAGE_UPLOAD_DIR

PROFILE_IMAGE_UPLOAD_DIR
------------------------

Default: ``"profile_images/"``

Name of the directory where profile images are stored. Base directory is :setting:`DATA_ROOT`.


.. setting:: BOOKTYPE_CONVERTER_MODULES

BOOKTYPE_CONVERTER_MODULES
--------------------------

List of plugins for book conversions into different formats.

Example::

    BOOKTYPE_CONVERTER_MODULES = (
        'booktype.convert.converters',
    )


.. setting:: REDIS

Redis 
=====

Configuration for connecting to Redis database.


.. setting:: REDIS_HOST

REDIS_HOST
----------

Default: ``"localhost"``.


.. setting:: REDIS_PORT

REDIS_PORT
----------

Default: ``6379``.


.. setting:: REDIS_DB

REDIS_DB
--------

Default: ``1``.


.. setting:: REDIS_PASSWORD

REDIS_PASSWORD
--------------

Default: ``None``.


Rest of the settings
====================


.. setting:: COMPRESS_ENABLED

COMPRESS_ENABLED
----------------

Used for configuring ``django_compressor`` application. "Dev" profile has compression disabled by default.


.. setting:: COMPRESS_OFFLINE

COMPRESS_OFFLINE
----------------

Used for configuring ``django_compressor`` application. "Dev" profile has compression disabled by default.


.. setting:: DEPRECATED

Deprecated
==========

We don't use these settings anymore but they are still here for compatibility issues.

BOOKI_NAME
----------

BOOKI_ROOT
----------

BOOKI_URL
---------

THIS_BOOKI_SERVER
-----------------

BOOKI_MAINTENANCE_MODE
----------------------
   
