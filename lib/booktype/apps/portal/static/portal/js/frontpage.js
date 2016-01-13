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

(function (win, $, _) {
  'use strict';

  $(function () {
    $('.books-widget button.showGrid').click(function () {
      $('.books-widget .showing-books').removeClass('book-list');
      $('.books-widget .showing-books').addClass('book-thumb');
      $('.books-widget .showing-books').nextAll().removeClass('book-list');
      $('.books-widget .showing-books').nextAll().addClass('book-thumb');
    });

    $('.books-widget button.showList').click(function () {
      $('.books-widget .showing-books').removeClass('book-thumb');
      $('.books-widget .showing-books').addClass('book-list');
      $('.books-widget .showing-books').nextAll().removeClass('book-thumb');
      $('.books-widget .showing-books').nextAll().addClass('book-list');
    });
    $('.front-page .books-widget button.create-book').click(function () {
      win.location.href = $(this).attr('data-href');
    });

    $('.front-page .groups-widget button.create-group').click(function () {
      win.location.href = $(this).attr('data-href');
    });

  });

})(window, jQuery, _);
