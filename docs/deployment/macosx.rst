Installing Booktype on Mac OS X
===============================

Instructions were tested on Mac OS X 10.5, 10.6 and 10.8. We assume your
Python Virtual Environment is called 'mybooktype' and your Booktype
project is called 'mybook'. Feel free to change it.

Be careful you have correct access permissions.

You **MUST** install Homebrew and you **MUST** install Xcode or Command
Line Development Tools.

::

     http://mxcl.github.com/homebrew/

You **MUST** figure out for yourself how to start Redis and PostgreSQL
server installed with Homebrew. Write 'brew info redis' for more
information.

Booktype with Sqlite3
---------------------

This example works with Sqlite3 and Python built in web server. This
method is not recommended for production server.

How to install
~~~~~~~~~~~~~~

::

    # Install needed packages
    brew install git redis libjpeg libpng libxml2

    # Create Python Virtual Environment and install needed Python modules
    virtualenv --distribute mybooktype
    cd mybooktype
    source bin/activate

    # For Mac OS X 10.8
    # There is a problem with 10.8 and you MUST do this. Version of library might be different.
    pip install lxml --install-option="--with-xml2-config=/usr/local/Cellar/libxml2/2.8.0/bin/xml2-config"

    # If you don't have 10.8 you can try to do just this
    pip install lxml

    # Install rest of Python packages
    pip install Django==1.3 South==0.7.5 unidecode PIL

    # Fetch Booktype source
    git clone https://github.com/booktype/Booktype.git

    # Create Booktype project
    ./Booktype/scripts/createbooktype --database sqlite mybook

    # Initialise Booktype
    source mybook/booktype.env
    django-admin.py syncdb --noinput
    django-admin.py migrate
    django-admin.py loaddata documentation_licenses
    django-admin.py createsuperuser

    # Start server
    django-admin.py runserver 0.0.0.0:8080

How to run it again
~~~~~~~~~~~~~~~~~~~

::

    cd mybooktype
    source bin/activate
    source mybook/booktype.env
    django-admin.py runserver 0.0.0.0:8080

Booktype with PostgreSQL
------------------------

This example works with PostgreSQL and Python built in web server.
Version of PostgreSQL server depends of your distribution. This method
is recommended for production server.

Be aware this has not been fully tested.

How to install
~~~~~~~~~~~~~~

::

    # Install needed packages
    brew install git redis libjpeg libpng libxml2 postgresql

    # Create Python Virtual Environment and install needed Python modules
    virtualenv --distribute mybooktype
    cd mybooktype
    source bin/activate

    # For Mac OS X 10.8
    # There is a problem with 10.8 and you MUST do this. Version of library might be different.
    pip install lxml --install-option="--with-xml2-config=/usr/local/Cellar/libxml2/2.8.0/bin/xml2-config"

    # If you don't have 10.8 you can try to do just this
    pip install lxml

    # Install rest of Python packages
    pip install Django==1.3 South==0.7.5 unidecode PIL psycopg2

    # Fetch Booktype source
    git clone https://github.com/booktype/Booktype.git

    # Create Booktype project
    ./Booktype/scripts/createbooktype --database postgresql mybook

    # Create PostgreSQL user and enter password
    /usr/local/bin/createuser -SDRP booktype

    # Create PostgreSQL database
    /usr/local/bin/createdb -E utf8 -O booktype booktype

You will need to enter database info in the settings file. Edit
mybooktype/mybook/settings.py file and put this as database info (you
will need to enter username password also).

::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'booktype',                      
            'USER': 'booktype',
            'PASSWORD': 'ENTER PASSWORD HERE',
            'HOST': 'localhost',
            'PORT': ''
        }
    }

You can continue now with initialisation.

::

    source mybook/booktype.env
    django-admin.py syncdb --noinput
    django-admin.py migrate
    django-admin.py loaddata documentation_licenses
    django-admin.py createsuperuser

    # Run server
    django-admin.py runserver 0.0.0.0:8080

How to run it again
~~~~~~~~~~~~~~~~~~~

::

    cd mybooktype
    source bin/activate
    source mybook/booktype.env
    django-admin.py runserver 0.0.0.0:8080

