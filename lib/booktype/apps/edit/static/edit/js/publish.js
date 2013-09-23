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

(function(win, jquery, _) {

	jquery.namespace('win.booktype.editor.publish');

  win.booktype.editor.publish = function() {

        /*******************************************************************************/
        /* SHOW                                                                        */
        /*******************************************************************************/

        var _show = function() {
          win.booktype.ui.notify('Loading');

          // set toolbar
          var t = win.booktype.ui.getTemplate('templatePublishHeader');
          jquery("DIV.contentHeader").html(t);


          var t2 = win.booktype.ui.getTemplate('templatePublishContent');
          jquery("#content").html(t2);

          // Show tooltips
          jquery("DIV.contentHeader [rel=tooltip]").tooltip({container: 'body'});

          jquery("#content button.btn-publish").on('click', function() {
              win.booktype.ui.notify('Publishing book');

              win.booktype.sendToCurrentBook({"command": "publish_book",
                                              "book_id": win.booktype.currentBookID},
                                              function(data) {
                                                  console.log(data);
                                                  win.booktype.ui.notify();
                                              });
          });

          window.scrollTo(0, 0);
        }

        /*******************************************************************************/
        /* HIDE                                                                        */
        /*******************************************************************************/

        var _hide = function() {
          // Destroy tooltip
          jquery("DIV.contentHeader [rel=tooltip]").tooltip('destroy');

          // Clear content
          jquery('#content').empty();
          jquery("DIV.contentHeader").empty();

        }

        /*******************************************************************************/
        /* INIT                                                                        */
        /*******************************************************************************/

        var _init = function() {
            jquery("#button-publish").on('change', function(e) { win.booktype.editor.showPublish(); });
      
        }

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {'init': _init,
            'show': _show,
            'hide': _hide,
            'name': 'publish'};

  }();

  
})(window, jQuery, _);