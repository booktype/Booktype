# How to use Booktype with Nginx

For more information consult the Django documentation at: 
* https://code.djangoproject.com/wiki/DjangoAndNginx
* https://docs.djangoproject.com/en/dev/howto/deployment/fastcgi/

Example commands are for Debian/Ubuntu based system. It is recommended to use Supervisor (http://supervisord.org/) or similar software (Upstart on Ubuntu) to control your Gunicorn or FastCGI processes.

# As Gunicorn

Let us imagine our Booktype project is installed in _/var/www/mybooktype/mybook/_ directory. This directory should be owned by user who is going to run gunicorn_django process (probably www-data).

    # Install needed packages
    sudo apt-get install nginx 

    # Copy configuration file
    cp /var/www/mybooktype/mybook/gunicorn.nginx /etc/nginx/sites-available/booktype

    # Edit configuration file
    # You should change: server_name and fastcgi_pass
    vi /etc/nginx/sites-available/booktype

    # Enable your Booktype site 
    ln -s /etc/nginx/sites-available/booktype /etc/nginx/sites-enabled/booktype
   
    # Restart Nginx
    service nginx restart

    # Activate Python Virtual Environment (IF YOU ARE USING IT)
    source /var/www/mybooktype/bin/activate

    # Install Gunicorn
    pip install gunicorn
    
    # Load environment variables
    source /var/www/mybooktype/mybook/booki.env

    # Start Gunicorn (Basic example)
    gunicorn_django -b 127.0.0.1:8000 -w 4


# As FastCGI

Let us imagine our Booktype project is installed in _/var/www/mybooktype/mybook/_ directory. 

    # User www-data should be owner
    sudo chown -R www-data:www-data /var/www/mybooktype/mybook/

    # Install needed packages
    sudo apt-get install nginx

    # Copy configuration file
    cp /var/www/mybooktype/mybook/fastcgi.nginx /etc/nginx/sites-available/booktype

    # Edit configuration file
    # You should change: server_name and fastcgi_pass
    vi /etc/nginx/sites-available/booktype

    # Enable your Booktype site 
    ln -s /etc/nginx/sites-available/booktype /etc/nginx/sites-enabled/booktype
   
    # Restart Nginx
    service nginx restart

    # Activate Python Virtual Environment (IF YOU ARE USING IT)
    source /var/www/mybooktype/bin/activate

    # Install Flup  (http://www.saddi.com/software/flup/)
    pip install flup

    # Load environment variables
    source /var/www/mybooktype/mybook/booki.env

    # Start FastCGI process (Basic example)
    django-admin.py runfcgi host=127.0.0.1 port=8000 

# Possible problems

* Trying to use manage.py instead of django-admin.py.
* Not loading environment variables before running Gunicorn or FastCGI process.
