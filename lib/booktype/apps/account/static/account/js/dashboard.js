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

        $('#bookCreationWizard').steps({
          headerTag: 'h3',
          bodyTag: 'section',
          transitionEffect: 'slideLeft',
          autoFocus: true,
          showFinishButtonAlways: true,
          onFinished: function (event, currentIndex) {
            if (finishButtonEnabled) {
              var createBookForm = $('#createBookModal form').get(0);
              var formData = new FormData(createBookForm);

              // attach import file if create mode is Import Docx/Epub
              var creationMode = $("#createBookModal [name=creation_mode]:checked").val();
              var files = $('#book-file').data('files');

              if (creationMode === 'based_on_file' && files.length > 0)
                 formData.append('import_file', files[0]);

              $.ajax({
                url: createBookForm.action,
                type: 'POST',

                // Form data
                data: formData,
                contentType: false,
                processData: false,

                success: function(data) {
                  // TODO: show notification or indicator of loading when notifications are improved
                  win.location.href = data.redirect;
                },
                error: function() {
                  // TODO: improve notifications
                  var errorMsg = win.booktype._('errorOnCreateBookMessage', 'Unexpected error while creating the book')
                  win.booktype.utils.alert(errorMsg);
                }
              });
            }
          },
          onStepChanged: function (event, currentIndex, priorIndex) {
            if (!finishButtonEnabled) {
              toggleFinishBtn(false);
            }
          },
          onStepChanging: function (event, currentIndex, newIndex) {
            //STEP 3: Creation mode
            if (currentIndex === 2) {
              var creationMode = $("input[type=radio][name=creation_mode]:checked").val();
              if (creationMode === 'based_on_book') {
                var baseBook = $('#id_base_book').val();
                return (baseBook.length > 0);
              }
            }

            return true;
          },
          labels: {
            next: win.booktype._('next', 'Next'),
            previous: win.booktype._('previous', 'Previous'),
            finish: win.booktype._('finish', 'Finish')
          }
        });
      }

      handleSteps();

      // bind modal shown to disable finish button
      $(document).on('shown.bs.modal', '#createBookModal', function () {
        //enable tooltips in modal
        $('[data-toggle=tooltip]').tooltip({container: 'body'});

        self.finishButton = $('a[href="#finish"]', createBookModal);
        toggleFinishBtn(false);
      });

      $(document).on('change', 'input[type=radio][name=creation_mode]', function() {
        // removing class which adjust height
        $('.wizard .content').removeClass('importMode');

        switch (this.value) {
          case 'based_on_book':
            $('#base_on_book_row').show();
            $('#base_on_skeleton_row').hide();
            $('#base_on_file_import_row').hide();
            break;

          case 'based_on_skeleton':
            $('#base_on_skeleton_row').show();
            $('#base_on_book_row').hide();
            $('#base_on_file_import_row').hide();
            break;

          case 'based_on_file':
            $('#base_on_file_import_row').show();
            $('#base_on_book_row').hide();
            $('#base_on_skeleton_row').hide();

            // add class to adjust height in wizard container
            $('.wizard .content').addClass('importMode');

            break;

          default:
            // default: 'scratch'
            $('#base_on_book_row').hide();
            $('#base_on_skeleton_row').hide();
            break;
        }
      });

      // clean on close modal
      $(document).on('hide.bs.modal', '#createBookModal', function () {
        // clearing the input
        $('#bookCreationWizard form :input')
          .not(':button, :submit, :reset')
          .not('[name="csrfmiddlewaretoken"]')
          .removeAttr('checked')
          .removeAttr('selected')
          .not(':checkbox, select')
          .val('')
          .removeAttr('value');
        $('#bookCreationWizard form .roles-options .btn').removeClass('active');
        $('#book_base_row').hide();

        $('#bookCreationWizard').steps('destroy');
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
            .removeClass('default-cursor disabled');
        } else {
          self.finishButton.parent().attr('aria-disabled', true).addClass('disabled');
          self.finishButton
            .addClass('default-cursor disabled');
        }
      }

      // BOOK IMPORT

      // this is to set the name of file to be imported
      function setFilename(files) {
        var bookFilename = $('.book_filename');
        if (files.length > 0) {
          bookFilename.find('b').html(files[0].name);
          bookFilename.removeClass('hidden');
        } else
          bookFilename.addClass('hidden');
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

      function validateFile(file) {
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

        $(this).addClass('dragover');
      });

      $(document).on('drop dragleave', '#drag-area', function (e) {
        e.preventDefault();
        $(this).removeClass('dragover');
      });

      // attach files when drop event
      $(document).on('drop', '#drag-area', function (e) {
        e.preventDefault();
        var files = e.originalEvent.dataTransfer.files;

        // set file to input field to then send the file to server
        $('#book-file').data('files', files);

        // set the filename just for graphic effects
        setFilename(files);
      });

      // attach files when picking with the file input
      $(document).on('change', '#book-file', function () {
        var files = this.files;

        $('#book-file').data('files', files);

        // set the filename just for graphic effects
        setFilename(files);
      });

      var importButton = $('#import');
      var congratsMsg = $('.congrats');
      var dragArea = $('#drag-area');

      // jquery fileupload
      $('#book-file').fileupload({
        dataType: 'json',
        sequentialUploads: true,
        dropZone: dragArea,
        pasteZone: dragArea,
        done: function (e, data) {
          var result = data.result;

          // delay required to not overwrite "progressall" things
          setTimeout(function () {
            // hide progressbar
            $('#processing-alert').addClass('hidden');

            // success import, redirect if there are no errors and warnings
            if (result.errors.length <= 0 && result.warnings.length <= 0) {
              congratsMsg.removeClass('hidden');
              win.location.href = result.url;
            }

            // show alert messages in popup
            if (result.infos.length > 0)
              showAlerts(result.infos, 'infos');

            // if warnings, show alerts and `view the book` button if possible
            if (result.warnings.length > 0) {
              showAlerts(result.warnings, 'warnings');

              if (result.errors.length <= 0) {
                congratsMsg.removeClass('hidden');

                $('#view_imported_book')
                  .attr('href', result.url)
                  .removeClass('hidden');

                importButton.addClass('hidden');
              }
            }

            if (result.errors.length > 0) showAlerts(result.errors, 'errors');

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

          if (data.files.length === 0) return;

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
      // TODO: create a better scope for all these elements, looks ugly now
      $(document).on('hidden.bs.modal', '#importBookModal', function () {
        importButton.removeClass('hidden');

        $('.book_title').val('');
        $('[type="checkbox"]').removeAttr('checked');
        $('.alert, #progress-bar-container, .book_filename').addClass('hidden');

        if ($('#book_filename').length > 0) $('#book_filename')[0].files = [];
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
          $('#create-group-btn').trigger('click');
        }
      });

      // initialize the dashboard router
      new DashboardRouter();

      // Start Backbone history, necessary for bookmarkable URL's
      Backbone.history.start();
    },

    // this is made to join books via InviteCodes
    join_book: function () {
      // handle form submit
      $('#submitCode').on("click", function () {
        var container = $('#joinBookModal');
        var form = container.find('form');
        var url = form.attr('action');
        var params = form.serialize();

        // let's hide alert just in case
        container.find('.alert').addClass('hide');

        $.post(url, params, function (data) {
          if (data.result) {
            container.modal('hide');
            win.booktype.utils.alert(data.message, 400);
          } else
            container.find('.alert').removeClass('hide');
        });
      });

      // just reload after clicking accept in alert window.
      // TODO: find out a better way to achieve this
      $(document).on('click', '.btn.acceptText', function () {
        window.location.reload();
      })
    }
  };

  // on ready
  $(function () {
    win.booktype.dashboard.init();

    // bind and handle join books with invite codes
    win.booktype.dashboard.join_book();
  });

})(window, jQuery);
