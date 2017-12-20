===================
Development profile
===================


Booktype comes with already predefined development profile and a list of requirements for it.


Lazy development setup
----------------------

Our development setup should look as much as possible as the production setup but it is possible to do development with the minimalistic setup also.

Check the :doc:`deployment documentation </deployment/index>` which external services and libraries you need to install and have running.

.. code-block:: bash

    # Create Python Virtual Environment
    $ virtualenv --distribute bk20
    $ cd bk20
    $ source  bin/activate

    # Clone Booktype
    $ git clone https://github.com/booktype/Booktype.git

    # Install Python requirements for development profile
    $ pip install -r Booktype/requirements/dev.txt 

    # Create Booktype project with development profile using Sqlite3
    $ ./Booktype/scripts/createbooktype -p dev -d sqlite bkdev
    $ cd bkdev

    # Initialise project
    $ ./manage.py syncdb
    $ ./manage.py migrate
    $ ./manage.py update_permissions
    $ ./manage.py update_default_roles

    # Edit bkdev_site/settings/dev.py file if needed

    # Collect static files
    $ ./manage.py collectstatic

    # Run built-in web server in one shell
    $ ./manage.py runserver 0.0.0.0:8000

    # Run workers in another shell
    $ ./manage.py celeryd -E --autoreload

