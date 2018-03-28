Installing Booktype 2.3
-----------------------

Booktype is web-based software which means you do not install it on the author's 
computer; instead, authors access the Booktype server through a web browser. For 
writing and editing books, authors can use any computer or mobile device with a 
browser such as [Mozilla Firefox](https://www.mozilla.org/firefox/) or
[Google Chrome](https://www.google.com/chrome/).

The Booktype server can be installed on various GNU/Linux distributions and
Mac OS X. Packages for [Debian](https://www.debian.org) and
[Ubuntu](https://www.ubuntu.com) GNU/Linux are in preparation.


Simple Dev Install
------------------

Instructions for a simple dev install on Debian 8 can be found on
[Digital Ocean's community site](https://www.digitalocean.com/community/tutorials/how-to-publish-real-books-with-booktype-on-debian-8).


Database setup
--------------

Before you can install your own Booktype server, you will need a database to be 
available. [PostgreSQL](https://www.postgresql.org) is the recommended database
management system for production servers.

 [Setting up the database](https://sourcefabric.booktype.pro/booktype-23-for-authors-and-publishers/setting-up-the-database/)


Manual installation
-------------------

Installation from the git repository is recommended for development and 
testing.

 [GNU/Linux](https://sourcefabric.booktype.pro/booktype-23-for-authors-and-publishers/manual-installation-on-gnulinux/)

 [Mac OS X](https://sourcefabric.booktype.pro/booktype-23-for-authors-and-publishers/manual-installation-on-os-x/)

Installation using docker
--------------------------

Installation with docker can be found on 
[Bookstype-docker](https://github.com/booktype/booktype-docker)

PDF renderer installation
-------------------------

Booktype 2.1 can use a variety of renderers to convert HTML book sources into 
PDF. [mPDF](https://github.com/mpdf/mpdf) must be installed separately from Booktype
in a directory such as /var/www/mpdf/ and the Booktype server configured for 
the installation path. 

**mPDF** library requires php GD library installed 
[GD installation](http://php.net/manual/en/image.installation.php)

