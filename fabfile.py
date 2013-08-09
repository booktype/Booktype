#!/usr/bin/env python

from fabric.api import *

# TODO, posebno za migrate itd..

# fab deploy_dev
# fab deploy_test

@hosts(['aco@booktype-dev.sourcefabric.org:2219'])
def deploy_dev():
    with cd('/home/www-data/source/Booktype/'):
        sudo("git pull origin devel", user="www-data")
        
    sudo("service apache2 restart")


@hosts(['aco@booktype-test.sourcefabric.org:2217'])
def deploy_test():
    with cd('/home/www-data/source/Booktype/'):
        sudo("git pull origin devel", user="www-data")
        
    sudo("service apache2 restart")


