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

If upgrading from older Booktype (1.6) version to 2.0 should install first requirements
in legacy.txt, run South migrations and then install one of the above (prod.txt or dev.txt)

    pip install -r requirements/legacy.txt
