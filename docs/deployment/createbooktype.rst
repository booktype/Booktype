==============
Createbooktype
==============

Createbooktype is a command-line utility for creating :doc:`Booktype projects </deployment/structure>` with automatically generated configuration files.

Usage
=====

.. code-block:: bash

    createbooktype [--database <type>|--check-versions] <project location>

<project location> can be the full path to the project location or the name of the project.

Example:

=======================   =====================
argument                  project name
=======================   =====================
*/var/www/mybk*           mybk
*bk20*                    bk20
*../bk20*                 bk20
=======================   =====================

.. note::

   The user must have write permissions to create or write to the project location. If the project location already exists it will just create the needed files.

Options
=======

.. code-block:: bash

    --help

Show help message and exit.

.. code-block:: bash

    --quiet

Do not show any messages.

.. code-block:: bash

    --verbose

Show messages.

.. code-block:: bash

    --database <type>

Configure *Project* to use specific database backend. Options are: "postgres", "postgresql", "sqlite".

.. code-block:: bash

    --check-versions

Check versions of packages

.. code-block:: bash

    --virtual-env VIRTUAL_ENV

Specifies the default VIRTUAL_ENV


Examples of usage
=================

This will create a project called **bk2** in the current directory. It will use the PostgreSQL database as a backend by default.

.. code-block:: bash

    $ ./scripts/createbooktype bk2


This will create a project called **mybk** in the /var/www/ directory using Sqlite3 as a backend.

.. code-block:: bash

    $ ./scripts/createbooktype --database sqlite3 /var/www/mybk/
