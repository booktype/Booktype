====
MOBI
====

Booktype can export books in  `MOBI format <https://en.wikipedia.org/wiki/Mobipocket>`_ using external 3rd party software. User has choice between `Calibre`_ (GNU General Public License v3) and `KindleGen`_ from Amazon. `Calibre`_ is enabled by default.

User is required to install 3rd party software on its own.

Use Calibre
===========

Configuration options::

    MOBI_CONVERT = "calibre" 
    CALIBRE_PATH = "ebook-convert"
    CALIBRE_ARGS = ""


**MOBI_CONVERT** instructs Booktype to use `Calibre`_ for MOBI export.

**CALIBRE_PATH** defines full path to the command line tool used for conversion. By default it is configured as if `Calibre`_  is installed on the system and globally accessible. In case it is not, user can define full path to the ebook-convert tool.

**CALIBRE_ARGS** defines extra arguments for the ebook-convert tool. Extra arguments are available here: http://manual.calibre-ebook.com/cli/ebook-convert.html.


Use KindleGen
=============

Configuration options::

    MOBI_CONVERT = "kindlegen" 
    KINDLEGEN_PATH = "kindlegen"

**MOBI_CONVERT** instructs Booktype to use `KindleGen`_ for MOBI export.

**KINDLEGEN_PATH** defines full path to the command line tool used for conversion. By default it is configured as if `KindleGen`_ is installed on the system and globally  accessible. In case it is not, user can define full path to the kindlegen tool.


.. _Calibre: http://calibre-ebook.com
.. _KindleGen: http://www.amazon.com/gp/feature.html?docId=1000765211
