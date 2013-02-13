# Debian

Instructions were tested on Debian 6. 

Be careful you have correct access permissions. We assume your Python Virtual Environment is called 'mybooktype' and your Booktype project is called 'mybook'. Feel free to change it.

## Booktype with Sqlite3

This example works with Sqlite3 and Python built in web server. This method is not recommended for the production server.

### How to install

    # Install needed packages as root
    apt-get install python python-dev sqlite3 git-core python-pip python-virtualenv 
    apt-get install redis-server libxml2-dev libxslt-dev

    # Create Python Virtual Environment
    virtualenv --distribute mybooktype
    cd mybooktype
    source bin/activate

    # Fetch Booktype source
    git clone https://github.com/sourcefabric/Booktype.git

    # Install needed python modules
    pip install -r Booktype/requirements/sqlite.txt

    # Create Booktype project
    ./Booktype/scripts/createbooki --database sqlite mybook

    # Initialise Booktype
    source mybook/booki.env
    django-admin.py syncdb --noinput
    django-admin.py migrate
    django-admin.py createsuperuser

### Deploy using built in web server (not recommended but good for testing)

    # This has to be done every time you want to start a server
    cd mybooktype
    source bin/activate
    source mybook/booki.env
    django-admin.py runserver 0.0.0.0:8080

### Deploy using Apache (recommended)
    
    # Install needed packages
    apt-get install apache2-mpm-prefork libapache2-mod-wsgi

You need to modify _mybook/booki.wsgi_ file. This will not be needed in version 1.5.4 and more. Be careful and add full path to the _mybooktype/bin/activate_this.py_ file. Add this after the _sys.path.insert_ line:

    activate_this = 'FULL_PATH_TO/mybooktype/bin/activate_this.py' 
    execfile(activate_this, dict(__file__=activate_this))

Copy configuration file:

    # Copy configuration file
    cp mybooktype/mybook/wsgi.apache /etc/apache2/sites-available/booktype

    # User www-data should be the owner
    chown -R www-data:www-data mybooktype/
    
    # Edit configuration file
    # You need to add name of the server 
    vi /etc/apache2/sites-avilable/booktype

    # Add your new site
    a2ensite booktype

    # Restart Apache server
    service apache2 restart

## Booktype with PostgreSQL

This example works with PostgreSQL and Python built in web server. Version of PostgreSQL server depends of your distribution. This method is recommended for the production server.

### How to install

    # Install needed packages as root 
    apt-get install python python-dev sqlite3 git-core python-pip python-virtualenv 
    apt-get install redis-server libxml2-dev libxslt-dev postgresql python-psycopg2

    # Create Python Virtual Environment and install needed python modules
    virtualenv --distribute mybooktype
    cd mybooktype
    source bin/activate

    # Fetch Booktype source
    git clone https://github.com/sourcefabric/Booktype.git

    # Install needed python modules
    pip install -r Booktype/requirements/postgresql.txt

    # Create Booktype project
    ./Booktype/scripts/createbooki --database postgresql mybook

    # Become PostgreSQL user
    su - postgres

    # Create PostgreSQL user and enter password
    createuser -SDRP booktype

    # Create PostgreSQL database
    createdb -E utf8 -O booktype booktype

    # Exit from being PostgreSQL user
    exit

Allow connections to database booktype for user booktype. This can depend of your requirements. Edit /etc/postgresql/8.4/main/pg_hba.conf  (full file name depends of PostgreSQL version) file and put this inside.

    local   booktype    booktype                      md5

Restart PostgreSQL server after this.

    service postgresql restart

You will need to enter database info in the settings file. Edit mybooktype/mybook/settings.py file and put this as database info (you will need to enter username password also).

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

    source mybook/booki.env
    django-admin.py syncdb --noinput
    django-admin.py migrate
    django-admin.py createsuperuser

### Deploy using built in web server (not recommended but good for testing)

    # This has to be done every time you want to start a server
    cd mybooktype
    source bin/activate
    source mybook/booki.env
    django-admin.py runserver 0.0.0.0:8080

### Deploy using Apache (recommended)
    
    # Install needed packages
    apt-get install apache2-mpm-prefork libapache2-mod-wsgi

You need to modify _mybook/booki.wsgi_ file. This will not be needed in version 1.5.4 and more. Be careful and add full path to the _mybooktype/bin/activate_this.py_ file. Add this after the _sys.path.insert_ line:

    activate_this = 'FULL_PATH_TO/mybooktype/bin/activate_this.py' 
    execfile(activate_this, dict(__file__=activate_this))

Copy configuration file:

    # Copy configuration file
    cp mybooktype/mybook/wsgi.apache /etc/apache2/sites-available/booktype

    # User www-data should be the owner
    chown -R www-data:www-data mybooktype/
    
    # Edit configuration file
    # You need to add name of the server 
    vi /etc/apache2/sites-avilable/booktype

    # Add your new site
    a2ensite booktype

    # Restart Apache server
    service apache2 restart