# Translating Booktype interface

There are two components of Booktype to translate: *lib/booki* and *lib/booktypecontrol*. 

Booktype is a Django application and all rules for translating other Django applications should apply as well. For more info please check this document https://docs.djangoproject.com/en/1.4/topics/i18n/translation/.

## Checkout the Booktype repository

If you have Github account you can just fork Booktype repository. You should checkout *devel* branch.

     git clone -b devel https://github.com/sourcefabric/Booktype.git

## New directories

Create new locale directories (e.g. *locale/de/LC_MESSAGES/* for German) for each component.
    
     mkdir -p Booktype/lib/booki/locale/de/LC_MESSAGES/

## Create message file

Then in each component directory run the makemessages command (You might have to install a few gettext packages first, before the above command will work), eg for German:

     cd Booktype/lib/booki/
     django-admin.py makemessages -l de

     cd ../../Booktype/lib/booktypecontrol/
     django-admin.py makemessages -l de
    
You should end up with two untranslated .po files:

     Booktype/lib/booki/locale/de/LC_MESSAGES/django.po
     Booktype/lib/booktypecontrol/locale/de/LC_MESSAGES/django.po


## Update info

Update the header information in the commented part at the top of each file.


## Start translating 

Load these .po files into [Poedit](http://www.poedit.net/) and start translating. Enter the team contact information and language into your poedit *Edit -> Preferences and Catalog -> Settings*, they will be added to the file.

When you save in [Poedit](http://www.poedit.net/), django.mo files will be compiled. 

## Send changes

Now you can send .po and .mo files to the Booktype team (). If you have Github account you should send pull request to the Booktype team.
