Installing Booktype 2.0
-----------------------

Booktype is web-based software which means you do not install it on the author's 
computer; instead, authors access the Booktype server through a web browser. For 
writing and editing books, authors can use any computer or mobile device with a 
browser such as [Mozilla Firefox](http://www.mozilla.org/firefox/) or 
[Google Chrome](http://www.google.com/chrome/).

The Booktype server can be installed on various GNU/Linux distributions and
Mac OS X. Packages for [Debian](http://www.debian.org) and 
[Ubuntu](http://www.ubuntu.com) GNU/Linux are in preparation.


Simple Dev Install
------------------

Instructions for a simple dev install on Debian 8 can be found on [Digital Ocean's community site](https://www.digitalocean.com/community/tutorials/how-to-publish-real-books-with-booktype-on-debian-8)

Database setup
--------------

Before you can install your own Booktype server, you will need a database to be 
available. [PostgreSQL](http://www.postgresql.org) is the recommended database 
management system for production servers.

 [Setting up the database](http://sourcefabric.booktype.pro/booktype-20-for-authors-and-publishers/setting-up-the-database/)


Manual installation
-------------------

Installation from the git repository is recommended for development and 
testing.

 [GNU/Linux](http://sourcefabric.booktype.pro/booktype-20-for-authors-and-publishers/installation-on-gnulinux/)

 [Mac OS X](http://sourcefabric.booktype.pro/booktype-20-for-authors-and-publishers/installation-on-os-x/)

PDF renderer installation
-------------------------

Booktype 2.0 can use a variety of renderers to convert HTML book sources into 
PDF. [mPDF](http://www.mpdf1.com) must be installed separately from Booktype 
in a directory such as /var/www/mpdf/ and the Booktype server configured for 
the installation path. 
