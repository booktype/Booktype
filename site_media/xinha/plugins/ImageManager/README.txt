Originally Developed by: http://www.zhuo.org/htmlarea/

> This is a plug-in for HTMLArea 3.0
> 
> The PHP ImageManager + Editor provides an interface to 
> browser for image files on your web server. The Editor
> allows some basic image manipulations such as, cropping,
> rotation, flip, and scaling.
> 
> Further and up-to-date documentation can be found at
> http://www.zhuo.org/htmlarea/docs/index.html
> 
> Cheer,
> Wei

2005-03-20 
  by Yermo Lamers of DTLink, LLC (http://www.formvista.com/contact.html)

Please post questions/comments/flames about this plugin in the Xinha forums
at 

   http://xinha.gogo.co.nz/punbb/viewforum.php?id=1

------------------------------------------------------------------------------
If you have GD installed and configured in PHP this should work out of the 
box. 

For production use see config.inc.php for configuration values. You will 
want to adjust images_dir and images_url for your application.

For demo purposes ImageManager is set up to view images in the

   /xinha/plugins/ImageManager/demo_images

directory. This is governed by the images_dir and images_url config options.

The permissions on the demo_images directory may not be correct. The directory
should be owned by the user your webserver runs as and should have 755 
permissions.

--------------------------------------------------------------------------------

By  default this ImageManager is set up to browse some graphics
in plugins/ImageManager/demo_images.

For  security reasons image uploading is turned off by default.
You can enable it by editing config.inc.php.

---------------------------------
For Developers
---------------------------------

CHANGES FROM Wei's Original Code:

Single Backend:								 
---------------

All  requests  from  the javascript code back to the server now
are  routed  through  a  single  configurable  backend  script,
backend.php.

Request URLs are of the form:

 <config backend URL>(?|&)__plugin=ImageManager&__function=<function>&arg=value&arg=value

The default URL is plugins/xinha/backend.php.

This  approach  makes  it  possible  to  completely replace the
backend  with  a  perl  or ASP implementation without having to
change any of the client side code.

You  can  override  the  location  and  name of the backend.php
script by setting the config.ImageManager.backend property from
the  calling  page. Make sure the URL ends in an "&". The code,
for now, assumes it can just tack on variables.

For  the moment the javascript files in the assets directory do
not  have access to the main editor object and as a result have
not  access to the config. For the moment we use a _backend_url
variable  output  from  PHP  to communicate the location of the
backend  to  these  assets.  It's  a  kludge. Ideally all these
config  values  should  be  set  from  the  calling page and be
available through the editor.config.ImageManager object.

Debug Messages
---------------

The  php files include a simple debugging library, ddt.php. See
config.inc.php  for  how  to  turn  it on. It can display trace
messages to the browser or dump them to a log file.

I'll  try  to  package  up  the client-side tracing-to-textarea
_ddt()  functions  I've  put  together.  Having a trace message
infrastructure has always served me well.

-------------
Flakey Editor
-------------

The  editor  I  use  is  flakey  (but  very  very fast). It has
problems with tab to space conversion so if the indenting looks
weird that's why.

----
TODO
----

ImageManager really needs a complete rewrite. 

. ImageManager should appear in a pane instead of a popup
  window using Sleeman's windowpane support.

.  html  and  php code are intermixed. It would be very nice to
use  some  kind  of templating for the dialogs; this templating
should be done long hand so it can be re-used regardless of the
backend implementation language.

.  the  config  should  probably  be  some format that would be
easily  read  by  multiple  implementations of the back end. It
would  be nice to have a single configuration system regardless
of whether the backend is PHP, Perl or ASP.

.  javascript assets are not objects. Passing config options to
the  assets  functions requires intermediate variables which is
really  ugly.  Everything should be cleanly integrated into the
object heirarchy akin to the way Linker is done.

.  if  an  image is selected from the document editor window it
should  be  focused  and  highlighted  in  the  image selection
window.

. fix fully-qualified url in image selection box under MSIE.

. per-image permissions. We should include some kind of backend
permissions      management      so      users     can     only
delete/edit/move/rename images that they have uploaded.

. add a CANCEL button and a SAVE AS button to the editor.

.  add  a  list view akin to EFM. (and include image properties
width/height/depth/etc.)

.  figure  out  a way for ImageManager to work "out of the box"
regardless of install.

. client-side tracing.

. fancy stuff like adding a UI to define rollovers, animations,
etc.

