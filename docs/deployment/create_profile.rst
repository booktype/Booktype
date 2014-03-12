================
Creating project
================

.. We need separate page which will cover in full all the options and usage for createbooktype script.

:doc:`Createbooktype </deployment/createbooktype>` is a script which creates new Booktype projects. It creates entire project structure on the disk with auto generated configuration files. 


Example of usage
================

This will create project called **bk2** in current directory. It will use PostgreSQL database as a backend and automatically be set in production profile.

.. code-block:: bash

    $ ./scripts/createbooktype  bk2


This will create project called **mybk** in /var/www/ directory. It will use Sqlite3 as a backend and will be set in development profile.

.. code-block:: bash
  
    $ ./scripts/createbooktype --database sqlite3  --profile dev /var/www/mybk/
