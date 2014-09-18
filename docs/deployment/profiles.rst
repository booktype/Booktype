========
Profiles
========


What are they and why we need them
==================================

Project could be deployed using different profiles. Why would we need them in the first place? 

Let us imagine we were hired by a community of writters to extend their Booktype installation with additional features.

Our first step would be to create :doc:`Booktype project <structure>`. This project would be used as a base for our future development. When we are working and developing new features on our local machine we would use **development profile**. When we are happy with new changes we would like to show them and test them somewhere. This is where our **staging profile** comes. That is for instance profile we use on a staging machine where our customers can test new features. When they are happy with what we have done we deploy the same project to production using **production profile**.

This means our project can be deployed using different settings depending if we are developing it on our local machine or running it in the production. In our **development profile** we can include additional django debug applications, including Django admin application, disable access to some public API our custom code is using or use different backend for storing data. In our **production profile** system we can disable all the debugging options, extra logging we needed during the development phase and allow access to public API our custom code needs.

As you can see, profiles are just different Django settings files in which you configure your application for different environments.


Custom profile
==============

Each profile is a new Django settings file. 

We want to create new profile "maintanance". There are better ways how to do it but in our over simplified example we will create new profile which will define new set of configuration options and files to show one static page "Please wait. Site in maintanance mode.".

First we need new settings file in *$PROJECT/settings/maintanance.py*. Make it by copying content of already existing profile dev.

Then change this options in the settings:

.. code-block:: python

    ROOT_URLCONF = '{}.urls.maintanance'.format(BOOKTYPE_SITE_DIR)

Then we need to change existing *manage.py* file in the project root to use new profile.

.. code-block:: python

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "$PROJECT.settings.maintanance")

At the end we need to define our URL dispatcher in *$PROJECT/url/maintanance.py* file.

.. code-block:: python    

    from django.conf.urls import patterns, url, include
    from django.views.generic import TemplateView

    urlpatterns = patterns('',
        (r'^$', TemplateView.as_view(template_name="our_message.html")),
    )

