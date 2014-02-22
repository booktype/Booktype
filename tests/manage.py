#!/usr/bin/env python
import os
import sys

from unipath import Path

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    BASE_DIR = Path(os.path.abspath(__file__)).parent

    sys.path.insert(0, BASE_DIR)
    sys.path.insert(0, BASE_DIR.parent.child('lib'))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
