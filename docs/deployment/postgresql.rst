==========
PostgreSQL
==========



How to create PostgreSQL database
=================================

Check the documentation: https://docs.djangoproject.com/en/dev/ref/databases/ .


#. Install PostgreSQL and Python modules::

    $ apt-get install  postgresql python-psycopg2

#. Change the password for PostgreSQL. This you need to do ``ONLY`` if you don't already know the password::

    $ sudo su postgres -c psql template1
    template1=# ALTER USER postgres WITH PASSWORD 'password';
    template1=# \q
 
    $ sudo passwd -d postgres
    $ sudo su postgres -c passwd 

#. Create PostgreSQL user "booktype"::

    $ sudo su postgres -c createuser booktype

#. Create database named "booktype" where user "booktype" is owner. This could depend of your OS version and can ask for another template::    

    $ createdb -D template1 -E utf8 -O booktype booktype

#. Allow connections to database booktype for user booktype. This can depend of your requirements::    

     $ vi /etc/postgresql/*/main/pg_hba.conf  (full file name depends of PostgreSQL version)

     local   booktype    booktype                      md5

#. Restart PostgreSQL::

    $ service postgresql restart


How to do it on Ubuntu
======================

The following instructions were tested on Ubuntu Lucid 10.04 and slightly differ from the generic instructions above.

#. Install PostgreSQL and Python modules::

    $ sudo apt-get install postgresql python-psycopg2

#. Change the password for PostgreSQL. This you need to do ``ONLY`` if you don't already know the password::    

    $ sudo -u postgres psql postgres
    postgres=# \password postgres
    postgres=# \q

    $ sudo passwd -d postgres
    $ sudo su postgres -c passwd

#. Create PostgreSQL user "booktype"::

    $ sudo -u postgres createuser -SDR booktype

#. Create database named "booktype" where user "booktype" is owner::

    $ sudo -u postgres createdb -E utf8 -O booktype booktype

#. Allow connections to database booktype for user booktype::

    $ sudo nano /etc/postgresql/8.4/main/pg_hba.conf  (exact file name depends on PostgreSQL version)

    local   booktype    booktype                         md5

#. Restart PostgreSQL::

    $ sudo invoke-rc.d postgresql-8.4 restart
