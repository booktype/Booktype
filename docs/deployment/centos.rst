Installing Booktype on CentOS
=============================

Instructions were tested on CentOS 6.3.

Be careful you have correct access permissions. We assume your Python
Virtual Environment is called 'mybooktype' and your Booktype project is
called 'mybook'. Feel free to change it.

Before you start installing check your documentation how to add EPEL
repository! For instance:

::

    su -c 'rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm'

You will also need to install "Development Tools":

::

    su -c 'yum groupinstall "Development Tools"'

Booktype with Sqlite3
---------------------

This example works with Sqlite3 and Python built in web server. This
method is not recommended for production server.

How to install
~~~~~~~~~~~~~~

::

    # Install needed packages 
    su -c 'yum -y install python python-devel sqlite git python-virtualenv python-pip'
    su -c 'yum -y install redis libxml2-devel libxslt-devel libjpeg libjpeg-devel zlib zlib-devel'

    # Create Python Virtual Environment and install needed Python modules
    virtualenv --distribute mybooktype
    cd mybooktype
    source bin/activate
    pip install Django==1.3 South==0.7.5 unidecode lxml PIL

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

Deploy using built in web server (not recommended but good for testing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # This has to be done every time you want to start a server
    cd mybooktype
    source bin/activate
    source mybook/booktype.env
    django-admin.py runserver 0.0.0.0:8080

Deploy using Apache (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Install needed packages
    yum install httpd mod_wsgi

Copy configuration file:

::

    cp mybooktype/mybook/wsgi.apache file into /etc/httpd/conf.d/booktype.conf

    # User www-data should be the owner
    chown -R apache:apache mybooktype/

    # Edit configuration file
    # You need to add name of the server and change log path to /var/log/httpd/ 
    vi /etc/httpd/conf.d/booktype.conf

    service httpd restart

If you will get permission errors you might need to disable SELinux
support. Please check CentOS documentation how to do that. You can also
check any documentation related to CentOS+Apache2+mod\_wsgi+Django
deployment.

Booktype with PostgreSQL
------------------------

This example works with PostgreSQL and Python built in web server.
Version of PostgreSQL server depends of your distribution. This method
is recommended for production server.

How to install
~~~~~~~~~~~~~~

::

    # Install needed packages 
    su -c 'yum -y install python python-devel sqlite git python-virtualenv python-pip'
    su -c 'yum -y install redis libxml2-devel libxslt-devel libjpeg libjpeg-devel zlib zlib-devel'
    su -c 'yum -y install postgresql-server postgresql-libs postgresql-devel python-psycopg2'

    # Create Python Virtual Environment and install needed python modules
    virtualenv --distribute mybooktype
    cd mybooktype
    source bin/activate
    pip install Django==1.3 South==0.7.5 unidecode lxml PIL psycopg2

    # Fetch Booktype source
    git clone https://github.com/booktype/Booktype.git

    # Create Booktype project
    ./Booktype/scripts/createbooktype --database postgresql mybook

    # Initialize PostgreSQL. ONLY if you did not have PostgreSQL installed before
    chkconfig postgresql on
    service postgresql initdb
    service postgresql start

    # Become postgres user
    su - postgres

    # Create PostgreSQL user and enter password
    createuser -SDRP booktype

    # Create PostgreSQL database
    createdb -E utf8 -O booktype booktype

    # Stop being Postgres user
    exit

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
            'HOST': '',
            'PORT': ''
        }
    }

Allow connections to database booktype for user booktype. This can
depend of your requirements. Edit /var/lib/pgsql/data/pg\_hba.conf file
and put this inside.

::

    local   booktype    booktype                      md5

Restart PostgreSQL server after this.

::

    service postgresql restart

You can continue now with initialisation.

::

    source mybook/booktype.env
    django-admin.py syncdb --noinput
    django-admin.py migrate
    django-admin.py loaddata documentation_licenses
    django-admin.py createsuperuser

Start redis

::

    chkconfig redis on
    service redis start

Deploy using built in web server (not recommended but good for testing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # This has to be done every time you want to start a server
    cd mybooktype
    source bin/activate
    source mybook/booktype.env
    django-admin.py runserver 0.0.0.0:8080

Deploy using Apache (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # Install needed packages
    yum install httpd mod_wsgi

Copy configuration file:

::

    cp mybooktype/mybook/wsgi.apache file into /etc/httpd/conf.d/booktype.conf

    # User www-data should be the owner
    chown -R apache:apache mybooktype/

    # Edit configuration file
    # You need to add name of the server and change log path to /var/log/httpd/ 
    vi /etc/httpd/conf.d/booktype.conf

    service httpd restart

If you will get permission errors you might need to disable SELinux
support. Please check CentOS documentation how to do that. You can also
check any documentation related to CentOS+Apache2+mod\_wsgi+Django
deployment.
