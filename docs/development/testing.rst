=====================
Booktype core testing
=====================


Setup
=====

.. We need to add link to page where we describe how to create project.

Booktype source comes with ready tests. To be able to run tests one must install required development dependencies 
(if already functional Booktype project does not exists). 

.. code-block:: bash

    $ virtualenv --distribute bkproject
    $ source bkproject/bin/activate
    $ pip install -r <PATH_TO_BOOKTYPE>/requirements/dev.txt
    $ cd <PATH_TO_BOOKTYPE>/tests


Tests
=====

This is for Unit tests and some Integration tests. Works with in memory Sqlite3 database. Does not require any external service to be running.

Discover runner is configured to use 'test_*.py' pattern to find available tests. Django settings file used for the tests is settings.py.

.. code-block:: bash

    $ ./start_tests.sh    


Configuration
-------------

Using *settings.py* file in *tests/* directory. Definition for URL is in *urls.py* file.


When to write them
------------------

Mainly when writing Unit Tests. Considering it uses Sqlite3 database it can also be used for some Integration tests which are working with database.


Example
-------

Example :repo:`lib/booktype/apps/core/tests/test_templatetags.py`.

.. code-block:: python

    import mock

    from django.test import TestCase

    from ..templatetags import booktype_tags

    class UsernameTest(TestCase):
        def test_anonymous(self):
            user = mock.Mock(username = 'Booktype')
            user.is_authenticated.return_value = False

            self.assertEquals(booktype_tags.username(user), "Anonymous")


        def test_no_firstname(self):
            user = mock.Mock(username='booktype', first_name='')
            user.is_authenticated.return_value = True

            self.assertEquals(booktype_tags.username(user), "booktype")



Functional Tests
================

This is for some Integration tests and all Functional tests . Works with in memory sqlite3 database out of the box but could/should be configured to work with PostgreSQL also. To run these tests you need to have running Redis, RabbitMQ, Celery workers. This also includes Selenium tests.

Discover runner is configured to use 'functest_*.py' pattern to find available tests. Django settings file used for the tests is func_settings.py.

.. code-block:: bash

    $ ./start_functests.sh


Configuration
-------------

Using *func_settings.py* file in *tests/* directory. Definition for URL is in *urls.py* file.


When to write them
------------------

For writing Integration tests and Functional tests. Tests are configured to use all external services (Redis, RabitMQ) and can Selenium can be freely used with them.

Write tests which are testing background workers for book conversion, communication with Sputnik, what our Web Server is returning to us, are we generating correct web pages and etc.


Example
-------

Example :repo:`lib/sputnik/tests/functest_connect.py`

.. code-block:: python

    import json

    from django.test import TestCase
    from django.core.urlresolvers import reverse
    from django.core.exceptions import PermissionDenied
    from django.contrib.auth.models import User

    import sputnik

    class ConnectTest(TestCase):
        ERROR_MESSAGE = {'messages': [], 'result': False, 'status': False}
        EMPTY_MESSAGE = {'messages': [], 'result': True, 'status': True}

        def setUp(self):
            self.dispatcher = reverse('sputnik_dispatcher')
            user = User.objects.create_user('booktype', 'booktype@booktype.pro', 'password')

        def test_anon_get_connect(self):
            response = self.client.get(self.dispatcher)

            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content, json.dumps(self.ERROR_MESSAGE))

        def test_get_connect(self):
            self.client.login(username='booktype', password='password')
            response = self.client.get(self.dispatcher, follow=True)

            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.content, json.dumps(self.ERROR_MESSAGE))



Rules when writing tests
========================

**Each test method tests one thing.** A test method must be extremely narrow in what it tests. A single test should never assert the behavior of multiple views, models, forms or even multiple methods within a class.

**For views when possible use the Request factory.** The *django.tets.client.RequestFactory* provides a wat to generate a request instance that can be used as the first argument to any view. This provides a greater amount of isolation then the standard Django test client, but it does require a little bit of extra work. 

.. code-block:: python

    from django.test import TestCase
    from django.test.client import RequestFactory

    class SimpleTest(TestCase):
        def test_details(self):
            factory = RequestFactory()

            request = factory.get('/customer/details')

**Don't write tests that have to be tested.**

**No Fixtures.** Working with fixtures can be problematic when we upgrade our models. New fixture data needs to be created plus all references to it (in the code and in the tests) must be updated. It is recommended to use tools for generating test data like Factory Boy (https://pypi.python.org/pypi/factory_boy/).

**Use mock objects.** In our Unit Tests we should use as much as possible mock objects (if it is possible). For that we use Python Mocking and Patching Library for Testing (https://pypi.python.org/pypi/mock).

More info
=========

* https://docs.djangoproject.com/en/dev/topics/testing/

* Tools

  * https://pypi.python.org/pypi/mock - A Python Mocking and Patching Library for Testing
  * https://pypi.python.org/pypi/factory_boy/ - A verstile test fixtures replacement based on thoughtbot's factory_girl for Ruby
  * https://pypi.python.org/pypi/django-discover-runner - A Django test runner based on unittest2's test discovery

* Books

  * http://chimera.labs.oreilly.com/books/1234000000754 - Test-Driven Development with Python
  * http://www.packtpub.com/python-testing-cookbook/book - Python Testing Cookbook
  * http://www.amazon.com/Python-Testing-Beginners-Daniel-Arbuckle/dp/1847198848 - Python Testing: Beginner's Guide
  * http://gettingstartedwithdjango.com/ - Getting Started with Django
  * http://effectivedjango.com/testing.html - Testing in Django
  * http://www.obeythetestinggoat.com/ - Objey the Testing Goat!
    
