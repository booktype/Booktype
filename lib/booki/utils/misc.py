# This file is part of Booktype.
# Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
#
# Booktype is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Booktype is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Booktype.  If not, see <http://www.gnu.org/licenses/>.

from django.template.defaultfilters import slugify
import os

def bookiSlugify(text):
    """
    Wrapper for default Django function. Default function does not work with unicode strings.

    @type text: C{string}
    @param: Text you want to slugify

    @rtype: C{string}
    @return: Returns slugified text
    """
    
    try:
        import unidecode

        text = unidecode.unidecode(text)
    except ImportError:
        pass

    return slugify(text)


def createThumbnail(fname, size = (100, 100)):
    """

    @type fname: C{string}
    @param: Full path to image file
    @type size: C{tuple}
    @param: Width and height of the thumbnail

    @rtype: C{Image}
    @return: Returns PIL Image object
    """

    import Image

    im = Image.open(fname)
    width, height = im.size
    
    if width > height:
        delta = width - height
        left = int(delta/2)
        upper = 0
        right = height + left
        lower = height
    else:
        delta = height - width
        left = 0
        upper = int(delta/2)
        right = width
        lower = width + upper
        
    im = im.crop((left, upper, right, lower))
    im.thumbnail(size, Image.ANTIALIAS)

    return im


def saveUploadedAsFile(fileObject):
    """
    Saves UploadedFile into file on disk.
    
    @type fileObject: C{UploadedFile}
    @param: Image file

    @rtype: C{Tuple}
    @return: Retursns file handler and file name as tuple
    """

    import tempfile

    fh, fname = tempfile.mkstemp(suffix='', prefix='profile')
        
    f = open(fname, 'wb')

    for chunk in fileObject.chunks():
        f.write(chunk)

    f.close()

    return (fh, fname)


def setProfileImage(user, fileObject):
    """
    Creates thumbnail image from uploaded file and saves it as profile image.
    
    @type user; C{django.contrib.auth.models.User}
    @param: Booktype user 
    
    @type fileObject: C{UploadedFile}
    @param: Image file
    """

    from django.conf import settings

    fh, fname = saveUploadedAsFile(fileObject)
        
    try:
        im = createThumbnail(fname, size = (100, 100))
        im.save('%s/%s%s.jpg' % (settings.MEDIA_ROOT, settings.PROFILE_IMAGE_UPLOAD_DIR, user.username), 'JPEG')

        # If we would use just profile.image.save method then out files would just end up with _1, _2, ... postfixes

        profile = user.get_profile()
        profile.image = '%s%s.jpg' % (settings.PROFILE_IMAGE_UPLOAD_DIR, user.username)
        profile.save()
    except:
        pass

    os.unlink(fname)


def getDirectorySize(dirPath):
    """
    Returns total file size of all files in this directory and subdirectories.
    
    @type dirPath; C{string}
    @param: Directory path
    
    @rtype text: C{int}
    @param: Returns total size of all files in subdirectories
    """
    
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(dirPath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    return total_size

