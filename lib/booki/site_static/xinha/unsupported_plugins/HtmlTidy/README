// Plugin for htmlArea to run code through the server's HTML Tidy
// By Adam Wright, for The University of Western Australia
//
//   Email:      zeno@ucc.gu.uwa.edu.au
//   Homepage:   http://blog.hipikat.org/
//
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).
//
// Version: 0.5
// Released to the outside world: 04/03/04


HtmlTidy is a plugin for the popular cross-browser TTY WYSIWYG editor,
htmlArea (http://www.interactivetools.com/products/htmlarea/). HtmlTidy
basically queries HTML Tidy (http://tidy.sourceforge.net/) on the
server side, getting it to make-html-nice, instead of relying on masses
of javascript, which the client would have to download.

Hi, this is a quick explanation of how to install HtmlTidy. Much better
documentation is probably required, and you're welcome to write it :)


* The HtmlTidy directory you should have found this file in should
  include the following:

  - README
        This file, providing help installing the plugin.

  - html-tidy-config.cfg
        This file contains the configuration options HTML Tidy uses to
        clean html, and can be modified to suit your organizations
        requirements.

  - html-tidy-logic.php
        This is the php script, which is queried with dirty html and is
        responsible for invoking HTML Tidy, getting nice new html and
        returning it to the client.

  - html-tidy.js
        The main htmlArea plugin, providing functionality to tidy html
        through the htmlArea interface.

  - htmlarea.js.onmode_event.diff
        At the time of publishing, an extra event handler was required
        inside the main htmlarea.js file. htmlarea.js may be patched
        against this file to make the changes reuquired, but be aware
        that the event handler may either now be in the core or
        htmlarea.js may have changed enough to invalidate the patch.
	
	UPDATE: now it exists in the official htmlarea.js; applying
	this patch is thus no longer necessary.

  - img/html-tidy.gif
        The HtmlTidy icon, for the htmlArea toolbar. Created by Dan
        Petty for The University of Western Australia.

  - lang/en.js
        English language file. Add your own language files here and
        please contribute back into the htmlArea community!

  The HtmlArea directory should be extracted to your htmlarea/plugins/
  directory.


* Make sure the onMode event handler mentioned above, regarding
  htmlarea.js.onmode_event.diff, exists in your htmlarea.js


* html-tidy-logic.php should be executable, and your web server should
  be configured to execute php scripts in the directory
  html-tidy-logic.php exists in.


* HTML Tidy needs to be installed on your server, and 'tidy' should be
  an alias to it, lying in the PATH known to the user executing such
  web scripts.


* In your htmlArea configuration, do something like this:

    HTMLArea.loadPlugin("HtmlTidy");

    editor = new HTMLArea("doc");
    editor.registerPlugin("HtmlTidy");


* Then, in your htmlArea toolbar configuration, use:

    - "HT-html-tidy"
        This will create the 'tidy broom' icon on the toolbar, which
        will attempt to tidy html source when clicked, and;

    - "HT-auto-tidy"
        This will create an "Auto Tidy" / "Don't Tidy" dropdown, to
        select whether the source should be tidied automatically when
        entering source view. On by default, if you'd like it otherwise
        you can do so programatically after generating the toolbar :)
        (Or just hack it to be otherwise...)
    

Thank you.

Any bugs you find can be emailed to zeno@ucc.gu.uwa.edu.au
