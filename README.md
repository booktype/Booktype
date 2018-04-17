Booktype
--------

Booktype makes it easier and quicker for authors, companies and organisations to edit and publish books. 
It imports DOCX or EPUB files, converts them into single-source HTML for online editing and proofreading, and uses CSS Paged Media to produce good-looking output for print, the open web, and almost any ebook reader, in seconds. Booktype facilitates collaborative, agile production across time zones and borders.

Booktype is built on the [Django](https://github.com/django/django) web framework and many great [Python libraries](https://github.com/booktype/Booktype/tree/master/requirements). The user interface is being [translated into many languages](https://www.transifex.com/sourcefabric/booktype) by our community.


More info
---------

- Check the [#booktype](https://twitter.com/search?q=%23booktype) hashtag on Twitter, or follow us [@Booktypo](https://twitter.com/Booktypo)      
- [Booktype manual](https://sourcefabric.booktype.pro/booktype-23-for-authors-and-publishers/)
- [Booktype issue tracker](https://dev.sourcefabric.org/browse/BK)
- [Booktype support forum](https://forum.sourcefabric.org/categories/booktype-support)
- [Booktype development forum](https://forum.sourcefabric.org/categories/booktype-development)
- [Booktype documentation forum](https://forum.sourcefabric.org/categories/booktype-documentation)


Installation
------------

Straightforward instructions to get you started on your first dev install of Booktype can be found [on the Digital Ocean community tutorials site](https://www.digitalocean.com/community/tutorials/how-to-publish-real-books-with-booktype-on-debian-8) and provide a clear path to getting an install running on a Debian machine.

Installation using Docker can be found at [Booktype-docker](https://github.com/booktype/booktype-docker)

Extra information can be found on the [online instructions](https://sourcefabric.booktype.pro/booktype-23-for-authors-and-publishers/before-you-install/) and in the [Booktype manual](https://sourcefabric.booktype.pro/booktype-23-for-authors-and-publishers/).


How to contribute
-----------------

1. Fork the [booktype/Booktype](https://github.com/booktype/Booktype/) repository. Please see GitHub
   [help on forking](https://help.github.com/articles/fork-a-repo) or use this [direct link](https://github.com/booktype/Booktype/fork) to fork.
2. Clone your fork to your local machine.
3. Create a new [local branch](https://help.github.com/articles/creating-and-deleting-branches-within-your-repository/).
4. Run tests and make sure your contribution works correctly.
5. Create a [pull request](https://help.github.com/articles/creating-a-pull-request) with details of your new feature, bugfix or other contribution.
6. Sign and return the contributor agreement paperwork, either for an [individual](https://github.com/booktype/contributor-agreements/raw/master/individual-contributor-license-agreement.pdf), or an [entity](https://github.com/booktype/contributor-agreements/raw/master/entity-contributor-license-agreement.pdf) such as a company, university or other organisation. This paperwork gives us the right to use your work in Booktype, and makes it clear that you retain ownership of the copyright in your contribution. 


Testing
-----------------

Booktype uses the [py.test](https://docs.pytest.org/en/latest/) testing framework with the [pytest-django](https://pytest-django.readthedocs.io/en/latest/) plugin. It makes the testing process easier, and also provides the ability to run ready-made django (unittest) tests.

To run tests:

1. Open a terminal and activate the virtual environment (Booktype must be installed).
2. Go to (cd command) instance root (folder with manage.py and pytest.ini file).
3. Run the **py.test** command. 
4. If you want pytest to print test coverage information, you should run **py.test --cov-report term-missing --cov=path/to/Booktype**. 
You can read more about coverage here: [pytest-cov](https://pypi.python.org/pypi/pytest-cov)


License
-------

Booktype is licensed under the [GNU AGPL license](LICENSE.txt).
