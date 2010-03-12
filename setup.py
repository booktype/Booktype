from setuptools import setup, find_packages

setup(
    name = "booki",
    version = "0.1",

    packages = find_packages('lib', 'lib/redis.py'),  # include all packages under src
    package_dir = {'':'lib'},   # tell distutils packages are under src

    author = "Andy Nicholson",
    author_email = "andy@infiniterecursion.com.au",

    description = "FLOSS Manuals collaborative book writing tool",
    url = "http://booki-dev.flossmanuals.net/",
    include_package_data = True,
    install_requires = [ 'simplejson', 'django' ],
    classifiers=[
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Programming Language :: Python",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
      ],
      keywords='collaborative book writing sprint',
      license='GPL',

)

