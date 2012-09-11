#/bin/sh
# Script for generating nightly Booktype snapshot packages
# Run from the directory containg the files checked out from git

VERSION=1.5.4~$(date "+%Y%m%d")
BUILDDEST=/tmp/booktype-${VERSION}/
DEBDIR=`pwd`/debian

git checkout devel
git pull

echo "cleaning up previous build..."

rm -rf /tmp/booktype-*
mkdir -p ${BUILDDEST}booktype

echo "copying files to temporary directory..."

cp -a * ${BUILDDEST}booktype || exit
cp -a $DEBDIR ${BUILDDEST}debian || exit

cd ${BUILDDEST} || exit

# Set the version of the snapshot package

sed -i "1s:(1.5.4-1):(${VERSION}):g" debian/changelog

# Fixes for 1.5.4  #############

# remove directories not needed by users
rm -r tests
rm -r tools

# moved to debian/copyright
rm AUTHORS.txt
rm LICENSE.txt
rm lib/booki/site_static/js/tiny_mce/classes/firebug/FIREBUG.LICENSE
rm lib/booki/site_static/js/tiny_mce/license.txt
rm lib/booki/site_static/js/jquery/AUTHORS.txt
rm lib/booki/site_static/js/jquery/MIT-LICENSE.txt
rm lib/booki/site_static/js/jquery/GPL-LICENSE.txt

#Fix permissions

#############################

echo "running the build..."

debuild -b -uc -us $@ || exit

# copy the new package to the public server
# scp /tmp/booktype_${VERSION}_all.deb apt.sourcefabric.org:/var/www/apt/snapshots/

# copy the build log too
# scp /tmp/booktype_${VERSION}_amd64.build apt.sourcefabric.org:/var/www/apt/snapshots/
