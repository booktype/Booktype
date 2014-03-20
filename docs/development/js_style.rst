================
JavaScript Style
================

Style
=====

There are many different JavaScript coding styles but we are using `Idiomatic JavaScript`_ style in Booktype. There is one exception, we do not use extra space inside parentheses.



How to check
=============

We are using `JSHint`_, a tool that helps to detech errors and potential problems in JavaScript code. 

First you need to install it:

.. code-block:: bash

    $ npm install jshint -g

We have prepared configuration file for our coding style in **scripts/jshintrc** file. You can either install it globally or specify path to the config file each time you execute jshint.

.. code-block:: bash

    $ jshint --config Booktype/scripts/jshintrc toc.js 

    toc.js: line 61, col 44, A leading decimal point can be confused with a dot: '.6'.
    toc.js: line 69, col 64, Strings must use singlequote.
    toc.js: line 77, col 49, Missing space after 'if'.
    toc.js: line 85, col 82, Strings must use singlequote.
    toc.js: line 85, col 102, Strings must use singlequote.
    toc.js: line 85, col 103, Trailing whitespace.
    toc.js: line 86, col 83, Strings must use singlequote.
    toc.js: line 87, col 79, Strings must use singlequote.
    toc.js: line 88, col 79, Strings must use singlequote.
    toc.js: line 88, col 88, Strings must use singlequote.
    toc.js: line 89, col 85, Strings must use singlequote.
    toc.js: line 91, col 80, Missing space after 'function'.


Read more in the official documentation how to integrate this tool inside of your text editor or IDE - http://www.jshint.com/install/.


Examples
========

Spaces
------

Never mix spaces and tabs. Please check your editor is correctly configured to use whitespace instead of tab. For readability we recommend setting two spaces representing a real tab.


Good
--------------------------

::

    if (condition) {
      doSomething();
    }

    while (condition) {
      iterating++;
    }

    var Chapter = Backbone.Model.extend({
      defaults: {
        chapterID: null,
        title: "",
        urlTitle: "",
        isSection: false,
        status: null
      }
    });

    this.refresh = function () {
      var $this = this,
        lst = win.booktype.editor.data.chapters.chapters;

      jquery.each(lst, function (i, item) {
        $this.refreshItem(item);
      });

      this._checkForEmptyTOC();
    };

    var DEFAULTS = {
      panels: {
        'edit': 'win.booktype.editor.edit',
        'toc' : 'win.booktype.editor.toc',
        'media' : 'win.booktype.editor.media'
      },

      styles: {
        'style1': '/static/edit/css/style1.css',
        'style2': '/static/edit/css/style2.css',
        'style3': '/static/edit/css/style3.css'
      },

      tabs: {
        'icon_generator': function (tb) {
          var tl = '';

          if (!_.isUndefined(tb.title)) {
            if (tb.isLeft) {
              tl = 'rel="tooltip" data-placement="right" data-original-title="' + tb.title + '"';
            } else {
              tl = 'rel="tooltip" data-placement="left" data-original-title="' + tb.title + '"';
            }
          }

          return '<a href="#" id="' + tb.tabID + '"' + tl + '><i class="' + tb.iconID + '"></i></a>';
        }
      }
    }







.. _Idiomatic JavaScript: https://github.com/rwaldron/idiomatic.js/
.. _JSHint: http://www.jshint.com/




