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
      function handleSteps() {
        // reset the basics
        finishButtonEnabled = false;
        $('.bookexists', createBookModal).css('display', 'none');

        $('#wizard-1').steps({
          headerTag: 'h3',
          bodyTag: 'section',
          transitionEffect: 'slideLeft',
          autoFocus: true,
          showFinishButtonAlways: true,
          onFinished: function (event, currentIndex) {
            if (finishButtonEnabled) {
              $('#createBookModal form').submit();
            }
          },
          onStepChanged: function (event, currentIndex, priorIndex) {
            if (!finishButtonEnabled) {
              toggleFinishBtn(false);
            }
          }
        });
      }

      handleSteps();

      // bind modal shown to disable finish button
      $(document).on('shown.bs.modal', '#createBookModal', function () {
        self.finishButton = $('a[href="#finish"]', createBookModal);
        toggleFinishBtn(false);
      });

      // clean on close modal
      $(document).on('hide.bs.modal', '#createBookModal', function () {
        // clearing the input
        $('#wizard-1 form :input')
          .not(':button, :submit, :reset')
          .not('[name="csrfmiddlewaretoken"]')
          .removeAttr('checked')
          .removeAttr('selected')
          .not(':checkbox, select')
          .val('')
          .removeAttr('value');
        $('#wizard-1 form .roles-options .btn').removeClass('active')

        $('#wizard-1').steps('destroy');
        handleSteps();
        createBookModal = $('#createBookModal');
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

      // bind keydown on title field to check book name availability
      $(document).on('keydown input', '.modal-dialog.new_book input[name="title"]', function () {
        win.booktype.initCSRF();

        setTimeout(function () {
          var title = $('.modal-dialog.new_book input[name="title"]').val();
          $.getJSON(createBookUrl, {
            'q': 'check',
            'bookname': title
          }).done(function (data) {
            if (data.available) {
              $('.bookexists', createBookModal).css('display', 'none');
              finishButtonEnabled = true;
            } else {
              if (title.length > 0) {
                $('.bookexists', createBookModal).css('display', 'block');
              }
              finishButtonEnabled = false;
            }
            toggleFinishBtn(finishButtonEnabled);
          });
        });

      });

      function toggleFinishBtn(enable) {
        if (enable === true) {
          self.finishButton.parent().attr('aria-disabled', false).removeClass('disabled');
          self.finishButton
            .removeClass('default-cursor disabled')
        } else {
          self.finishButton.parent().attr('aria-disabled', true).addClass('disabled');
          self.finishButton
            .addClass('default-cursor disabled')
        }
      }

      //BOOK IMPORT

      // this is to set the name of file to be imported
      function setFilename(files) {
        if (files.length > 0) {
          $('.book_filename b').html(files[0].name);
          $('.book_filename').removeClass('hidden');
        } else {
          $('.book_filename').addClass('hidden');
        }
      }

      // change the value of the progress bar
      function setProgress(container, progress) {
        var progressBar = container.find('.progress-bar');
        var progressLabel = progressBar.data('label');

        progressBar.attr('aria-valuenow', progress);
        progressBar.css('width', progress + '%');
        progressBar.find('.sr-only').html(progress + '% ' + progressLabel);
      }

      function showAlerts(messages, kind) {
        var container = $('#info-' + kind);
        var ul = container.find('ul');

        for (var i = 0; i < messages.length; i++) {
          var li = $(document.createElement('li'));
          li.text(messages[i]).appendTo(ul);
        }

        container.removeClass('hidden');
      }

      var validateFile = function (file) {

        var mimeType = file.type;
        var ALLOWED_EXTENSIONS = ['.epub', '.docx'];

        var name = file.name.toLowerCase();

        if ($.trim(mimeType) !== '') {
          return $.inArray(mimeType, allowedTypes) !== -1;
        }

        if (!_.some(_.map(ALLOWED_EXTENSIONS,
            function (val) {
              return name.indexOf(val, name.length - val.length) !== -1;
            }))) {
          return false;
        }

        return true;
      };

      $(document).on('dragenter dragover', '#drag-area', function (e) {
        e.stopPropagation();
        e.preventDefault();
      });

      $(document).on('drop', '#drag-area', function (e) {
        e.preventDefault();
        var files = e.originalEvent.dataTransfer.files;

        // set file to input field to then send the file to server
        $('#book-file').data('files', files);
      });

      var importButton = $("#import");

      // jquery fileupload
      $('#book-file').fileupload({
        dataType: 'json',
        sequentialUploads: true,

        done: function (e, data) {
          // delay required to not overwrite "progressall" things
          setTimeout(function () {
            // hide progressbar
            $('#processing-alert').addClass('hidden');

            // show alert messages in popup
            if (data.result.infos.length > 0) {
              showAlerts(data.result.infos, 'infos');
            }

            if (data.result.warnings.length > 0) {
              showAlerts(data.result.warnings, 'warnings');
            }

            if (data.result.errors.length > 0) {
              showAlerts(data.result.errors, 'errors');
            }

            // success import
            if (data.result.errors.length <= 0) {
              $('.congrats').removeClass('hidden');

              win.setTimeout(function () {
                win.location.href = data.result.url;
              }, 500);

            }
            // failed import
            else {
              // nothing for now
            }
          }, 600);
        },
        fail: function (e, data) {
          // delay required to not overwrite "progressall" things
          setTimeout(function () {
            $('#processing-alert').addClass('hidden');
            $('#something-wrong').removeClass('hidden');
          }, 600);
        },
        add: function (e, data) {
          // set filename
          setFilename(data.files);

          // clear/hide all alerts and progress bar
          $('#progress-bar-container, ' +
            '#processing-alert, ' +
            '#wrong-format, ' +
            '#something-wrong, ' +
            '#info-warnings, ' +
            '#info-infos, ' +
            '#info-errors, ' +
            '.congrats'
          ).addClass('hidden');

          $('#info-warnings, ' +
            '#info-infos, ' +
            '#info-errors'
          ).html('<ul></ul>');

          if (data.files.length === 0) {
            return;
          }

          // invalid file
          if (!validateFile(data.files[0])) {
            $('#wrong-format').removeClass('hidden');
            return;
          }

          importButton.removeClass('disabled');

          importButton.off('click').on('click', function () {
            win.booktype.initCSRF();
            data.submit();
            importButton.addClass('disabled');
          });
        },
        progressall: function (e, data) {
          var progress = parseInt(data.loaded / data.total * 100, 10);
          var container = $('#progress-bar-container');

          container.removeClass('hidden');
          setProgress(container, progress);

          if (progress === 100) {
            // let user see full progress and not hide it to fast
            setTimeout(function () {
              container.addClass('hidden');
              $('#processing-alert').removeClass('hidden');
            }, 500);
          }
        }
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
      new DashboardRouter();

      // Start Backbone history, necessary for bookmarkable URL's
      Backbone.history.start();
    }
  };

  // on ready
  $(function () {
    win.booktype.dashboard.init();
  });

})(window, jQuery);