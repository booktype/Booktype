/*
  This file is part of Booktype.
  Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
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

(function (win, jquery) {
  'use strict';
  jquery().ready(function () {

    jquery('.group .books-widget button.showGrid').click(function () {
      jquery('.group .books-widget .showing-books').removeClass('book-list');
      jquery('.group .books-widget .showing-books').addClass('book-thumb');
      jquery('.group .books-widget .showing-books').nextAll().removeClass('book-list');
      jquery('.group .books-widget .showing-books').nextAll().addClass('book-thumb');
    });

    jquery('.group .books-widget button.showList').click(function () {
      jquery('.group .books-widget .showing-books').removeClass('book-thumb');
      jquery('.group .books-widget .showing-books').addClass('book-list');
      jquery('.group .books-widget .showing-books').nextAll().removeClass('book-thumb');
      jquery('.group .books-widget .showing-books').nextAll().addClass('book-list');
    });

    jquery('button.join-group-button').click(function () {
        var groupName = jquery(this).attr('group-name-url');
        win.booktype.initCSRF();

        jquery.post(groupName, {
            task: 'join-group'
          }).done(function () {
            location.reload();
          });
      });

    jquery('button.leave-group-button').click(function () {
        var groupName = jquery(this).attr('group-name-url');
        win.booktype.initCSRF();

        jquery.post(groupName, {
            task: 'leave-group'
          }).done(function () {
            location.reload();
          });
      });


    jquery('button.group-settings-button').click(function () {
      window.location.href = jquery(this).attr('data-href');
    });
  });


})(window, jQuery);