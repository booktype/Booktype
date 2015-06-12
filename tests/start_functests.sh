#!/usr/bin/env sh

./func_manage.py test sputnik --pattern="functest_*.py"
./func_manage.py test booktype --pattern="functest_*.py"
./func_manage.py test booktypecontrol --pattern="functest_*.py"
