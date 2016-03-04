==============
Createbooktype
==============

Createbooktype is Booktype's command-line utility for creating :doc:`Booktype projects </deployment/structure>` on the disk with auto generated configuration files.

Usage
=====

.. code-block:: bash

    createbooktype [--database <type>|--profile <type>|--check-versions] <project location>

<project location> can be full path to project location or name of the project. 

Example:

=======================   =====================
argument                  project name
=======================   =====================
*/var/www/mybk*           mybk
*bk20*                    bk20
*../bk20*                 bk20
=======================   =====================

.. note::

   User must have write permissions to create or write to the project location. If project location already exists it will just create the needed files. 

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

    --profile <type>

Configure *Project* to use profile <type>. Options are: "dev", "prod".

.. code-block:: bash

    --check-versions

Check versions of packages

.. code-block:: bash

    --virtual-env VIRTUAL_ENV

Specifies the default VIRTUAL_ENV


Examples of usage
=================

This will create project called **bk2** in current directory. It will use PostgreSQL database as a backend and automatically be set i$

.. code-block:: bash

    $ ./scripts/createbooktype bk2


This will create project called **mybk** in /var/www/ directory. It will use Sqlite3 as a backend and will be set in development prof$

.. code-block:: bash

    $ ./scripts/createbooktype --database sqlite3  --profile dev /var/www/mybk/
