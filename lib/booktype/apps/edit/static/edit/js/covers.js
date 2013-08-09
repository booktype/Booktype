 /*
  This file is part of Booktype.
  Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
  Booktype is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  Booktype is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with Booktype.  If not, see <http://www.gnu.org/licenses/>.
*/

(function(win, jquery) {

	jquery.namespace('win.booktype.editor.covers');

  win.booktype.editor.covers = function() {

        /*******************************************************************************/
        /* SHOW                                                                        */
        /*******************************************************************************/

        var _show = function() {
          win.booktype.ui.notify('Loading');

          // set toolbar
          var t = win.booktype.ui.getTemplate('templateCoversToolbar');
          jquery("DIV.contentHeader").html(t);


          var t2 = win.booktype.ui.getTemplate('templateCoversContent');
          jquery("#content").html(t2);


          window.scrollTo(0, 0);
        }

        /*******************************************************************************/
        /* HIDE                                                                        */
        /*******************************************************************************/

        var _hide = function() {
          // clear content
          jquery('#content').empty();
          jquery("DIV.contentHeader").empty();

        }

        /*******************************************************************************/
        /* INIT                                                                        */
        /*******************************************************************************/

        var _init = function() {
            jquery("#button-cover").on('click', function(e) { win.booktype.editor.showCover(); });
      
        }

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {'init': _init,
            'show': _show,
            'hide': _hide,
            'name': 'covers'};

  }();

  
})(window, jQuery);