/*
  This file is part of Booktype.
  Copyright (c) 2014 Helmy Giacoman <helmy.giacoman@sourcefabric.org>
 
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

(function (win, $) {
  'use strict';
  win.booktype.dashboard = {
    init: function () {
      var self = this;
      var createBookModal = $('#createBookModal');
      var finishButtonEnabled = false;
      // set up create book wizard
      $('#wizard-1').steps({
        headerTag: 'h3',
        bodyTag: 'section',
        transitionEffect: 'slideLeft',
        autoFocus: true,
        showFinishButtonAlways: true,
        onFinished: function (event, currentIndex) {
          $('#createBookModal form').submit();
        },
        onStepChanged: function (event, currentIndex, priorIndex) {
          if (!finishButtonEnabled) {
            self.finishButton.attr('aria-disabled', true).addClass('disabled');
          }
        }
      });

      // bind modal shown to disable finish button
      $(document).on('shown.bs.modal', '#createBookModal', function () {
        $('a[href="#finish"]', createBookModal).parent().attr('aria-disabled', true).addClass('disabled');
        self.finishButton = $('a[href="#finish"]', createBookModal).parent();
      });

      // toggle grid or list view
      $(document).on('click', '.showList', function () {
        $('#books-prew, #books-prew-2').attr('class', 'book-list');
      });
      $(document).on('click', '.showGrid', function () {
        $('#books-prew, #books-prew-2').attr('class', 'book-thumb');
      });

      // add fade class when opening from button
      $(document).on('click', '#create-group-btn', function () {
        $('#createGroupModal').addClass('fade');
      });

      // bind keyup on title field to check book name availability
      $('input[name="title"]').keyup(function () {
        win.booktype.initCSRF();

        $.getJSON(createBookUrl, {
          'q': 'check',
          'bookname': $(this).val()
        }, function (data) {
          if (data.available) {
            $('.bookexists', createBookModal).css('display', 'none');
            finishButtonEnabled = true;
            self.finishButton.attr('aria-disabled', false).removeClass('disabled');
          } else {
            $('.bookexists', createBookModal).css('display', 'block');
            finishButtonEnabled = false;
            self.finishButton.attr('aria-disabled', true).addClass('disabled');
          }
        });
      });

      // Begin Backbone Router stuff
      var DashboardRouter = Backbone.Router.extend({
        routes: {
          'create-book':    'createBook',    // #create-book
          'settings':       'userSettings',  // #settings
          'create-group':   'createGroup'
        },

        createBook: function () {
          $('[data-target="#createBookModal"]').trigger('click');
        },

        userSettings: function () {
          $('#user-settings').trigger('click');
        },

        createGroup: function () {
          $('#createGroupModal').removeClass('fade');
          $('#create-group-btn').trigger('click');
        }
      });

      // initialize the dashboard router
      new DashboardRouter;

      // Start Backbone history, necessary for bookmarkable URL's
      Backbone.history.start();
    }
  };

  // on ready
  $(function () {
    win.booktype.dashboard.init();
  });

})(window, jQuery);