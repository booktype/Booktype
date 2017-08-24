Booktype
--------

Booktype makes it easier for people and organisations to collate, organise,
edit and publish books. Delivering frictionlessly to print,
[Amazon](https://amazon.com), [lulu.com](https://www.lulu.com/),
[iBooks](https://www.apple.com/ibooks/) and almost any ereader, Booktype
facilitates collaborative production processes. No more lost manuscripts,
overwritten Word files, awkward wikis or cumbersome CMSes.

Booktype is built on top of the Django web framework.


More info
---------

- Realtime chat on the #booktype channel on the [freenode.net](https://freenode.net/) server
- Check the [#booktype hashtag on Twitter](https://twitter.com/search?q=%23booktype.)      
- [Booktype manual](https://sourcefabric.booktype.pro/booktype-21-for-authors-and-publishers/)
- [Booktype issue tracker](https://dev.sourcefabric.org/browse/BK)
- [Booktype wiki](https://wiki.sourcefabric.org/display/Booktype/Booktype)
- [Booktype support forum](https://forum.sourcefabric.org/categories/booktype-support)
- [Booktype development forum](https://forum.sourcefabric.org/categories/booktype-development)
- [Booktype documentation forum](https://forum.sourcefabric.org/categories/booktype-documentation)


Installation
------------

Straightforward instructions to get you started on your first dev install of
Booktype can be found [on the Digital Ocean community tutorials site](https://www.digitalocean.com/community/tutorials/how-to-publish-real-books-with-booktype-on-debian-8)
and provide a clear path to getting an install running on a Debian 8 machine.

Extra information can be found on the [online instructions](https://sourcefabric.booktype.pro/booktype-21-for-authors-and-publishers/before-you-install/)
and in the [Booktype manual](https://sourcefabric.booktype.pro/booktype-21-for-authors-and-publishers/).


How to contribute
-----------------

Only 4 steps:

1. Fork the [sourcefabric/Booktype](https://github.com/sourcefabric/Booktype/) repository.
   [Help](https://help.github.com/articles/fork-a-repo) or [direct link](https://github.com/sourcefabric/Booktype/fork).
2. Clone your fork
3. Create new [local feature branch](https://help.github.com/articles/creating-and-deleting-branches-within-your-repository/).
4. Run tests.
5. Create [pull request](https://help.github.com/articles/creating-a-pull-request) with your feature/bugfix.


Testing
-----------------

Booktype using [py.test](https://docs.pytest.org/en/latest/) testing framework with [pytest-django](https://pytest-django.readthedocs.io/en/latest/) plugin,
it makes testing process easier and also gives ability to run already created django (unittest) tests.

To run tests:
1. Open terminal and activate virtual environment (Booktype must be installed).
2. Go to (cd command) instance root (folder with manage.py and pytest.ini file).
3. Run **py.test** command. 
4. If you want pytest to print test covarage information, you should run **py.test --cov-report term-missing --cov=path/to/Booktype**. 
You can read more about coverage here: [pytest-cov](https://pypi.python.org/pypi/pytest-cov)



License
-------

Booktype is licensed under the [AGPL license](LICENSE.txt).
