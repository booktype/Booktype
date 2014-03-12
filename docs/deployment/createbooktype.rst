==============
Createbooktype
==============

Createbooktype is Booktype's command-line utility for creating :doc:`Booktype Project </deployment/structure>`.

Usage
=====

.. code-block:: bash

    createbooktype [--database <type>|--profile <type>|--check-versions] <project location>


<project location>
~~~~~~~~~~~~~~~~~~~

This can be full path to project location or name of the project. 

Example:

=======================   =====================
argument                  project name
=======================   =====================
*/var/www/mybk*           mybk
*bk20*                    bk20
*../bk20*                 bk20
=======================   =====================

.. note::

   User must have write permissions to create or write to the project location. If project location already exists it will just create
   needed files. 


--quiet
~~~~~~~

Do not show any messages.


--verbose
~~~~~~~~~

Show messages.


--database <type>
~~~~~~~~~~~~~~~~~

Configure *Project* to use specific database backend. Options are: "postgres", "postgresql", "sqlite".


--profile <type>
~~~~~~~~~~~~~~~~

Configure *Project* to use profile <type>. Options are: "dev", "prod".


--check-versions
~~~~~~~~~~~~~~~~
