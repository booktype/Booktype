===========
Documenting
===========

`Sphinx`_ is used for documenting Booktype. The idea is to make our documentation readable (especially docstrings) in raw format. Developers looking at the documentation will spend their time in the editor. They do not want to look at cryptic text formatting which is only understandable after it has been converted to HTML. Having clean docstrings we make our documentation accessible both in HTML and raw format.


Markup
======

This document is not going to teach you how to use `Sphinx`_. For that we recommend looking at `First Steps`_ and `Sphinx documentation`_.

Here are couple of examples how you might want to format you Python Docstrings.


Arguments and return value
--------------------------

Between doc string and rest of the code it is allowed to have empty line to make code more readable.

.. code-block:: python

    def test_function(first, second):
        """This is my test function for the documentation.

        This test function does nothing at all. It is here just for the test purposes.
        There are many test functions but this function is special.

        :Args:
          - first (:class:`booktype.some.Class`): First argument
          - second: Second argument which also does nothing in test function

        :Returns:
          Returns list of elements. For example: [1, 2, 3, 4, 5]

        :Raises:
          KeyError: An error occurred while working with out arguments.
        """

        return [first, second, first + second]


Include code
------------

It is recommened to include code samples which could clarify usage of code we are trying to document.

.. code-block:: python

   def sample_function(a, b):
       """My sample function.

       .. code-block:: python

          a = 4 + 3
          ret = sample_function(a, 3)
          print ret
       """


Note
----

There is something  we want to emphasize? Use notes. It will nicely wrap your text in a block.

.. code-block:: python

    def sample_function(a, b):
        """My sample function.

        .. note::

           Please note this is only a sample function.
        """


Warnings
--------

There might be some issues when using this code? It could be dangerous if not used properly? Warned the user in that case! Your warning message will be wrapped in a block easily noticeable by user.

.. code-block:: python

    def sample_function(a, b):
        """My sample function.

        .. warning::

           This function is not working.
        """


Versions
--------

At some point we will have to modify or break our API. This we need to document.

.. code-block:: python

    def sample_function(a, b):
        """My sample function.

           .. versionadded:: 1.5
              We added new b argument.

           .. versionchanged:: 2.0
              Argument b can be also string.

           .. deprecated:: 3.1
              Use :func:`sample_function_new` instead.
        """


Reference other code
--------------------

Referencing other functions.

.. code-block:: python

    def sample_function(a, b):
        """My sample function.

           This function is similar to :func:`sample_function_new`.
        """

Referencing other classses or modules.

.. code-block:: python

    class SampleClass:
        """My sample class.

           This class is similar to :class:`booktype.sample.SampleClassNew`. 
           Module :mod:`booktype.contrib.sample` is used for 
        """

Sometimes we need to include a list of references or external documents. These lists are created using the seealso directive:

.. code-block:: python

    def sample_function(a, b):
        """My sample function.

           .. seealso::

              `GNU sample manual, Basic Sample Format <http://link>`_ Documentation for Sample Format.
        """


Building
========

.. note::

   Before doing these steps it is recommended to define environment variables **PYTHONPATH** and **DJANGO_SETTINGS_MODULE**.


.. code-block:: bash

    $ cd docs
    $ make html


Documentation will be in directory *_build/html/*.

.. _Sphinx: http://sphinx-doc.org/
.. _First Steps: http://sphinx-doc.org/tutorial.html
.. _Sphinx documentation: http://sphinx-doc.org/contents.html
