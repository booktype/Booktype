from setuptools import setup, find_packages

import os


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.md')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('AUTHORS.txt')
    )


setup(
    name="Booktype",
    version="2.4.0",

    packages=find_packages('lib'),  # include all packages under lib
    package_dir={'': 'lib'},   # tell distutils packages are under lib

    author="Aleksandar Erkalovic",
    author_email="aerkalov@gmail.com",

    description="Booktype is a free, open source platform that produces" + \
        "beautiful, engaging books formatted for print, Amazon, iBooks and" + \
        "almost any ereader within minutes.",
    long_description=long_description,

    url="http://booktype.sourcefabric.org/",
    include_package_data=True,
    package_data={
        # If any package contains *.txt or *.rst files, include them
        '': ['*.txt', '*.rst'],
    },
    scripts=['scripts/createbooktype'],

    install_requires=['setuptools', 'simplejson', 'django'],
    classifiers=[
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Programming Language :: Python",
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
      "Intended Audience :: Information Technology",
      "Framework :: Django",
      ],
      keywords='collaborative book writing sprint',
      license='AGPL',

)
