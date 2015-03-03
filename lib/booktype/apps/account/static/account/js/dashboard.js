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
      var allowedTypes = [
        'application/epub+zip',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ];

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
      $(document).on('keyup', '.modal-dialog.new_book input[name="title"]', function () {
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

      $(document).on('dragenter dragover', '#drag-area', function (e) {
        e.stopPropagation();
        e.preventDefault();
      });

      $(document).on('drop', '#drag-area', function (e) {
        e.preventDefault();
        var files = e.originalEvent.dataTransfer.files;

        // set file to input field to then send the file to server
        $('#book-file').data('files', files);

        // set the filename just for graphic effects
        setFilename(files);
      });

      $(document).on('change', '#book-file', function () {
        setFilename(this.files);
      });

      $(document).on('send_book', '#book-file', function () {
        // clear all alerts
        $('.alert').addClass('hidden');

        var uuid = $(this).data('upload-uuid');
        var url = $(this).data('status-url');

        var files = this.files;
        if (files.length === 0) {
          files = $(this).data('files');
        }

        // if files length is still zero, return
        if (files.length === 0) return;

        var mimeType = files[0].type;

        if ($.inArray(mimeType, allowedTypes) !== -1) {
          var form = $(this).closest('form');
          form[0].action += (form[0].action.indexOf('?') === -1 ? '?' : '&') + 'X-Progress-ID=' + uuid;

          win.booktype.initCSRF();

          var formData = new FormData(form[0]);
          formData.append('book_file', files[0]);

          $.ajax({
            url: form[0].action,
            type: 'POST',

            // Form data
            data: formData,
            contentType: false,
            processData: false,

            // Ajax events
            success: function (response) {
              // show alert messages
              if (response.infos.length > 0)
                showAlerts(response.infos, 'infos');

              if (response.warnings.length > 0)
                showAlerts(response.warnings, 'warnings');

              if (response.errors.length > 0)
                showAlerts(response.errors, 'errors');

              // hide progressbar and process alert
              win.setTimeout(function () {
                $('#processing-alert, #progress-bar-container').addClass('hidden');

                // redirect is no errors and warnings
                if (response.errors.length <= 0 && response.warnings.length <= 0) {
                  win.setTimeout(function () {
                    $('.congrats').removeClass('hidden');
                    win.location.href = response.url;
                  }, 500);
                }

                // if warnings, show button to view the book
                if (response.warnings.length > 0) {
                  $('.congrats').removeClass('hidden');

                  $('#view_imported_book')
                    .attr('href', response.url)
                    .removeClass('hidden');

                  $('#import').addClass('hidden');
                }
              }, 100);
            },

            error: function (response) {
              $('#something-wrong').removeClass('hidden');
            }
          });

          updateProgressInfo(url, uuid);

        } else {
          $('#wrong-format').removeClass('hidden');
          $('#import').removeClass('disabled');
          this.files = [];
        }
        return false;
      });

      $(document).on('click', '#import', function () {
        $('#book-file').trigger('send_book');
        $(this).addClass('disabled');
      });

      // reset content modal on close
      $(document).on('hidden.bs.modal', '#importBookModal', function () {
        $('.alert, #progress-bar-container, .book_filename').addClass('hidden');
        $('.book_title').val('');
        $('[type="checkbox"]').removeAttr('checked');

        if ($('#book_filename').length > 0) {
          $('#book_filename')[0].files = [];
        }
      });

      // Begin Backbone Router stuff
      var DashboardRouter = Backbone.Router.extend({
        routes: {
          'create-book': 'createBook', // #create-book
          'settings': 'userSettings', // #settings
          'create-group': 'createGroup'
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

  function updateProgressInfo(url, uuid) {
    $.getJSON(url, {
      'X-Progress-ID': uuid
    }, function (data, status) {
      var container = $('#progress-bar-container');
      console.log(data);
      if (data) {
        container.removeClass('hidden');
        var progress = parseInt(data.uploaded, 10) / parseInt(data.length, 10) * 100;
        setProgress(container, progress);

        if (data.length !== data.uploaded) {
          win.setTimeout(function () {
            updateProgressInfo(url, uuid);
          }, 1);
        }
      }

      if (data === null || data.length === data.uploaded) {
        setProgress(container, 100);

        // 2 seconds later, dismiss progressbar and show processing
        // book_file message
        $('#processing-alert').removeClass('hidden');
      }
    });
  }

  // this is to set the name of file to be imported
  function setFilename (files) {
    if (files.length > 0) {
      $('.book_filename b').html(files[0].name);
      $('.book_filename').removeClass('hidden');
    } else {
      $('.book_filename').addClass('hidden');
    }
  }

  // change the value of the progress bar
  function setProgress (container, progress) {
    var progressBar = container.find('.progress-bar');
    var progressLabel = progressBar.data('label');

    progressBar.attr('aria-valuenow', progress);
    progressBar.css('width', progress + '%');
    progressBar.find('.sr-only').html(progress + '% ' + progressLabel);
  }

  function showAlerts (messages, kind) {
    var container = $('#info-' + kind);
    var ul = container.find('ul');

    for (var i = 0; i < messages.length; i++) {
      var li = $(document.createElement('li'));
      li.text(messages[i]).appendTo(ul);
    }

    container.removeClass('hidden');
  }

})(window, jQuery);