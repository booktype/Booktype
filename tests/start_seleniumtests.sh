#!/usr/bin/env sh

./selenium_manage.py test sputnik --pattern="seltest_*.py"
./selenium_manage.py test booktype --pattern="seltest_*.py"
./selenium_manage.py test booktypecontrol --pattern="seltest_*.py"
