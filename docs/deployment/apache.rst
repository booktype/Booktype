===============
Apache settings
===============

This document will describe how to use Booktype with Apache and mod_wsgi.
For more information consult the Django documentation at: https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/modwsgi/ .

.. note::

   Example commands are for Debian/Ubuntu based system.


INSTALL
-------

#. Install Apache2. It is recommended to use Prefork MPM::

    $ apt-get install apache2-mpm-prefork

#. Install mod_wsgi::

    $ apt-get install libapache2-mod-wsgi

#. Create Booktype project.

#. Copy Apache configuration. We call it "booktype" for this example but you can call it anyway you like::

    cp /var/www/bk20/conf/wsgi.apache /etc/apache2/sites-available/booktype

#. Edit configuration file. You should change: ServerAdmin, ServerName, ... ::

    vi /etc/apache2/sites-available/booktype

#. Enable your Booktype site (when site name is "booktype")::

    a2ensite booktype

#. Restart Apache 2::

    service apache2 restart

