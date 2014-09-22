Booktype Requirements
---------------------

Booktype requires some specific Python dependencies in order to run correctly. 
Optionally, you may wish to install them in a virtualenv if you have other 
Python applications running on the system.

For a production system with a PostgreSQL database, please run the command:

    pip install -r requirements/prod.txt

Development systems with a SQLite database require a different selection of 
dependencies, which you can install with the command:

    pip install -r requirements/dev.txt
