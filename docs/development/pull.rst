==============================
Before you send a pull request
==============================


First step
----------

Besides doing the checks manually it is also possible to automatically validate some of the things before sending pull request.

At the moment script does:
  * Checks if modified Python code is according to PEP8 specification
  * Checks if modified JavaScript code is according to Booktype JavaScript specification
  * Creates and initialises Booktype instance
  * Executes Booktype tests

.. code-block:: bash

    $ scripts/before_pull_request.sh


Usage
=====

.. code-block:: bash

    $ scripts/before_pull_request.sh [-s|-n|-m]

-s
~~

Validates staged files in your repository. Result of **git diff --name-only --staged**.



-n
~~

Validates non staged files in your repository. Result of **git diff --name-only**.

-m
~~

Validates modified files. Result of **git status --porcelain**.


Examples
========

No problems with modified files::

    BEFORE PULL REQUEST 3000
    --------------------------------------------------------
    [*] Checking only staged files
        Seems like all the files are according to PEP8 and Booktype JavaScript standard.

    Press [Enter] key to start deployment...

Some of the files are not according to the specification::

    BEFORE PULL REQUEST 3000
    --------------------------------------------------------
    [*] Checking all modified files
        [jshint] /Booktype/lib/booktype/apps/edit/static/edit/js/booktype/covers.js
        [PEP8]   /Booktype/lib/booktype/apps/edit/views.py
        [PEP8]   /Booktype/fabfile.py

        Some of the files are not according to PEP8 or Booktype JavaScript standard. Fix the style only in your code.
        Create new ticket if style is broken in someone else's code and fix it later.

        Please check:
            - http://legacy.python.org/dev/peps/pep-0008/
            - Booktype docs 'docs/development/style.rst'
            - Booktype docs 'docs/development/js_style.rst'

    Press [Enter] key to start deployment...
