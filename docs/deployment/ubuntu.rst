========================
Ubuntu
========================

.. warning::

   Work in progress.

Instructions were tested on Ubuntu 10.04 and Ubuntu 12.04. 

Be careful you have correct access permissions. We assume your Python Virtual Environment is called 'mybooktype' and your Booktype project is called 'mybook'. Feel free to change it.

Booktype with Sqlite3
---------------------

This example works with Sqlite3 and Python built in web server. This method is not recommended for production server.

Install needed packages:

.. code-block:: bash

    $ sudo apt-get install python python-dev sqlite3 git-core python-pip python-virtualenv 
    $ sudo apt-get install libjpeg-dev zlib1g-dev redis-server libxml2-dev libxslt-dev

Create Python Virtual Environment:

.. code-block:: bash

    $ virtualenv --distribute mybooktype
    $ cd mybooktype
    $ source bin/activate

Fetch Booktype source:

.. code-block:: bash

    $ git clone https://github.com/sourcefabric/Booktype.git

Install needed Python modules:

.. code-block:: bash

    $ pip install -r Booktype/requirements/dev.txt

Create Booktype project:

.. code-block:: bash

     ./Booktype/scripts/createbooktype --database sqlite mybook

Initialise Booktype:

.. code-block:: bash

    $ ./manage.py syncdb --noinput
    $ ./manage.py migrate
    $ ./manage.py createsuperuser

Collects static files:

.. code-block:: bash

    $ ./manage.py collectstatic

Deploy using built in web server:

.. code-block:: bash

    $ ./manage.py runserver 0.0.0.0:8080

Run workers:

.. code-block:: bash
  
    $ ./manage.py celeryd -E --autoreload
