============
Python Style
============


Style
=====

`PEP 8`_ is the de-facto code style guide for Python. Django also has `Coding style`_ document which covers their coding style.

Just like in Django `Coding style`_  we don't use 79 characters limit for a line.


How to check
============

Conforming your Python code to `PEP 8`_ is generally a good idea and helps make code more consistent when working on projects with other developers.

If you don't have installed requirements for :doc:`development profile </development/profile>` you can manually install pep8 command-line tool.

.. code-block:: bash

    $ pip install pep8


Then run it on a file or series of files to get a report of any violations.

.. code-block:: bash

    $ pep8 --ignore=E501  apps/core/views.

    apps/core/views.py:3:1: E302 expected 2 blank lines, found 1
    apps/core/views.py:5:15: W291 trailing whitespace
    apps/core/views.py:6:1: W293 blank line contains whitespace
    apps/core/views.py:8:5: E101 indentation contains mixed spaces and tabs
    apps/core/views.py:8:5: W191 indentation contains tabs
    apps/core/views.py:9:5: E101 indentation contains mixed spaces and tabs
    apps/core/views.py:9:5: W191 indentation contains tabs
    apps/core/views.py:10:5: E101 indentation contains mixed spaces and tabs
    apps/core/views.py:10:5: W191 indentation contains tabs
    apps/core/views.py:11:5: E101 indentation contains mixed spaces and tabs
    apps/core/views.py:11:5: W191 indentation contains tabs
    apps/core/views.py:13:5: E101 indentation contains mixed spaces and tabs
    apps/core/views.py:13:5: W191 indentation contains tabs

Find out more about this command line tool: http://pep8.readthedocs.io/en/latest/.


Examples
========

Importing
---------

Importing is separated in 4 blocks:

* System import
* Django import
* 3rd party import
* Local import

There should be empty line between each block. Imports should usually be on separate lines.

.. code-block:: python

    # First we import system modules
    import os
    import sys
    import importlib

    # Then we import Django specific modeuls
    from django.http import HttpResponse
    from django.template.defaultfilters import slugify

    # After that we import 3rd party modules
    from ebooklib import epub

    # At the end we import Django app specific or library specific modules
    from . import loader
    from .base import BaseConverter


Documenting
-----------

We are using `Sphinx`_ for documenting Python code. We don't use special Sphinx directives for arguments because we want to have our documentation readable in the code also.

Between doc string and rest of the code it is allowed to have empty line to make code more readable.

Here is example for test function::

    def test_function(first, second):
        """This is my test function for the documentation.

        This test function does nothing at all. It is here just for the test purposes.
        There are many test functions but this function is special.

        .. code-block:: python

           test_function(booktype.someClass(), 21)

        :Args:
          - first (:class:`booktype.some.Class`): First argument
          - second: Second argument which also does nothing in test function

        :Returns:
          Returns list of elements. For example: [1, 2, 3, 4, 5]

        :Raises:
          KeyError: An error occurred while working with out arguments.
        """

        return [first, second, first + second]



Ignored variable
----------------        

If you need to assign something but will not need that variable, use _:

.. code-block:: python

    name, _ = unpack_userinfo()


Non public methods in class
---------------------------

When you want to have semi private methods or instance variables use leading underscore in the name.::

    class TestClass:
        def __init__(self):
            self._example_for_instance = 21
            self._initial_load()

        def _initial_load(self):
            do_something()


.. _PEP 8: http://www.python.org/dev/peps/pep-0008
.. _Sphinx: http://sphinx-doc.org/
.. _Coding style: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/