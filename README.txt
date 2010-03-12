FLOSS Manuals Booki
===================

A booki is like a wiki, but instead of ending up with a web page you get a book.  

Contents
========

lib/
  python modules, django application

tools/
  scripts for importing

tests/
  testing scripts

site_media/
  static web resources - JS, CSS, Xinha, images


INSTALLATION
------------
You can install Booki from PyPi via "easy_install booki" or from Git - a code versioning respository.

This assumes a Debian GNU/Linux server. If you have installed Booki via easy_install got to step 3.

0/ Obtain latest code from Git:

$git clone ssh://booki-dev.flossmanuals.net/var/cache/git/booki.git

You may need to switch to different branch in Git, like so
$ git checkout -t origin/sputnik

1/ Install Django - version 1.1.1, and SimpleJSON

$easy_install django 
$easy_install simplejson

2/ Instal the Redis Server - http://code.google.com/p/redis/

$apt-get install redis

3/ Customise settings.py

$cd {$BOOKI_INSTALL_PATH}/lib/booki
$cp settings.py.original settings.py
$vi settings.py

Pay attention to the database settings, eg db name, db username, db password, timezone 

4/ Configure the database

$./manage.py syncdb

5/ Start the test server via the console

$cd {$BOOKI_INSTALL_PATH}/lib/booki
$./manage.py runserver

Validating models...
0 errors found

Django version 1.1.1, using settings 'booki.settings'
Development server is running at http://127.0.0.1:8000/
Quit the server with CONTROL-C.

---
If you need to bind to a external IP and/or different port you can start the server like

$./manage.py runserver 10.1.1.1:4444

6/ Connect using the webserver to this URL , et viola, you have the Booki web interface.
