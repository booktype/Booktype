#/bin/sh
# Script for generating nightly Booktype snapshot packages
# Run from the directory containg the files checked out from git

VERSION=1.6.0~$(date "+%Y%m%d")
BUILDDEST=/tmp/booktype-${VERSION}/

git checkout devel
git pull

echo "cleaning up previous build..."

rm -rf /tmp/booktype-*
mkdir ${BUILDDEST}

echo "copying files to temporary directory..."

cp -a * ${BUILDDEST} || exit

cd ${BUILDDEST} || exit

# Set the version of the snapshot package

sed -i "1s:(1.6.0-1):(${VERSION}):g" debian/changelog

# Fixes for 1.6.0  #############

# remove directories not needed by users
rm -r tests
rm -r tools

# moved to debian/copyright
rm LICENSE.txt
rm lib/booki/site_static/js/tiny_mce/classes/firebug/FIREBUG.LICENSE
rm lib/booki/site_static/js/tiny_mce/license.txt
rm lib/booki/site_static/js/jquery/AUTHORS.txt
rm lib/booki/site_static/js/jquery/MIT-LICENSE.txt
rm lib/booki/site_static/js/jquery/GPL-LICENSE.txt

# remove Windows thumbnail files
rm lib/booki/site_static/images/jquerybubblepopup-theme/all-black/Thumbs.db
rm lib/booki/site_static/images/jquerybubblepopup-theme/all-black/ie/Thumbs.db
rm lib/booki/site_static/images/jquerybubblepopup-theme/green/Thumbs.db
rm lib/booki/site_static/images/jquerybubblepopup-theme/orange/Thumbs.db
rm lib/booki/site_static/images/jquerybubblepopup-theme/violet/Thumbs.db
rm lib/booki/site_static/images/jquerybubblepopup-theme/yellow/Thumbs.db

# fix permissions
chmod +x scripts/cron_reports.sh.original
chmod +x scripts/cron_reports_weekly.sh.original
chmod -x lib/booki/site_static/js/editor.js
chmod -x lib/booki/site_static/images/feed-icon-14x14.png

#############################

echo "running the build..."

debuild -b -uc -us $@ || exit

# copy the new package to the public server
# scp /tmp/booktype_${VERSION}_all.deb apt.sourcefabric.org:/var/www/apt/snapshots/

# copy the build log too
# scp /tmp/booktype_${VERSION}_amd64.build apt.sourcefabric.org:/var/www/apt/snapshots/
