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

	jquery.namespace('win.booktype.editor.media');

  win.booktype.editor.media = function() {
    var attachments;

    var drawAttachments = function() {
      var s = '';
      s += '<table width="100%">';
      jquery.each(attachments, function(i, item) {
        s += '<tr><td>'+item.name+"</td><td>"+win.booktype.utils.formatSize(item.size)+'</td></tr>';
      });
      s += '</table>'
      jquery("#content").html(s);

    }

    var _show = function() {
//      var t = win.booktype.ui.getTemplate("templateTOCToolbar");
      jquery("DIV.contentHeader").html('<h1>Media</h1>');

      win.booktype.sendToCurrentBook({"command": "attachments_list"}, function(data) {
        attachments = data.attachments;
        drawAttachments();
        window.scrollTo(0, 0);
        });
    }

    var _hide = function() {
      jquery('#content').empty();
      jquery("DIV.contentHeader").empty();
    }

    var _init = function() {
  
    }


    return {'init': _init,
            'show': _show,
            'hide': _hide,
            'name': 'media'};

  }();

  
})(window, jQuery);