(function (win, $) {
  'use strict';

  $.namespace('win.booktype.editor.settings');

  win.booktype.editor.settings = (function () {

    var SettingsRouter = Backbone.Router.extend({
      routes: {
        'settings': 'settings',
        'settings/:module': 'loadSetting'
      },

      settings: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['settings'];
          win.booktype.editor.data.activePanel.show();
        });
      },

      loadSetting: function (module, clearMessages) {
        clearMessages = (clearMessages === null) ? true : clearMessages;
        if (win.booktype.editor.settings.uiLoaded === undefined) {
          this.settings();
        }

        // load corresponding module
        var params = {
          'setting': module,
          'bookid': win.booktype.currentBookID
        };

        win.booktype.ui.notify('Loading section');

        $.get(win.booktype.bookSettingsURL + '?' + $.param(params))
          .fail(function (response) {
            _settingsLoadFailHandler(response);
          })
          .done(function (html) {
            var $settings = $('#setting_content');

            if (clearMessages === true)
              $settings.siblings('.alert').remove();

            $settings.html(html);
            $settings.trigger(module + '-loaded');

            // mark side menu option as active when loaded via url
            if ($('ul#settings').find('li.active').length === 0) {
              $('li:has(a[href="#' + module + '"])').addClass('active');
            }
          })
          .always(function(){
            if (clearMessages === true)
              win.booktype.ui.notify();
          });
      }
    });

    var router = new SettingsRouter();

    var _settingsLoadFailHandler = function (response) {
      var $settings = $('#setting_content');
      var notAvailable = '';

      if (response.status === 403) {
        notAvailable = win.booktype.ui.getTemplate('templatePermissionDenied');
      } else {
        notAvailable = win.booktype.ui.getTemplate('templateModuleNotAvailable');
      }
      $settings.html(notAvailable)
    };

    var _show = function () {
      $('#button-settings').addClass('active');

      var header = win.booktype.ui.getTemplate('templateSettingsHeader');
      $('DIV.contentHeader').html(header);

      var t = win.booktype.ui.getTemplate('templateSettingsContent');
      $('#content').html(t).addClass('settings');

      win.booktype.editor.settings.uiLoaded = true;
    };

    var _hide = function (callback) {
      $('#button-settings').removeClass('active');

      // Destroy tooltip
      $('DIV.contentHeader [rel=tooltip]').tooltip('destroy');

      // Clear content
      var $content = $('#content');
      $content.empty();
      $content.removeClass('settings');
      $('DIV.contentHeader').empty();

      win.booktype.sendToCurrentBook({'command': 'load_book_settings'},
        function (data) {
          // for now just update the needed one which is track changes
          win.booktype.trackChanges = data['track_changes'];

          if (!_.isUndefined(callback)) {
            callback();
          }
        });
    };

    var _init = function () {
      $('#button-settings').on('click', function () {
        Backbone.history.navigate('settings', true);

        // open default option
        var defaultMenu = $('#settings li a:first');
        if (defaultMenu.length > 0)
          win.booktype.utils.triggerClick(defaultMenu[0]);
      });

      $(document).on('shown.bs.tab', '#settings a[data-toggle="tab"]', function (e) {
        // trigger url via backbone router
        var option = $(e.target).attr('href').replace('#', '');
        router.navigate('settings/' + option, {
          trigger: true
        });
        return false;
      });

      $(document).on('click', '#saveBookSettings', function () {
        var $form = $(this).closest('form');
        var flashMessage = null;
        var setting = $form.find('input[name="setting"]').val();

        win.booktype.ui.notify(win.booktype._('loading_data', 'Loading data.'));
        $.ajax({
          type: 'POST',
          url: $form.attr('action'),
          data: $form.serialize(),
          success: function (resp) {
            var $container = $('#setting_content');

            if (resp.error) {
              if (resp.data !== undefined) {
                $container.empty().html(resp.data);
              } else {
                flashMessage = createFlash(resp.message, 'warning');
              }
            } else {
              // override setting variables
              switch (resp.updated_settings.submodule) {
                case 'language':
                  window.booktype.bookDir = resp.updated_settings.settings.dir;
                  window.booktype.bookLang = resp.updated_settings.settings.lang;
                  break;
              }

              // display success message and navigate
              reloadModule(setting);
              flashMessage = createFlash(resp.message, 'success');
              window.scrollTo(0, 0);
            }


            $container.siblings('.alert').remove();
            $container.before(flashMessage);

            win.booktype.ui.notify();
            dismissFlash();
          }
        });

        return false;
      });

      $(document).on('chapter-status-loaded', '#setting_content', function () {
        var $sortable = $('#setting_content .sortable-status');
        var $container = $(this);

        // Chapter status sortable
        $sortable.on('sortstop', function (event, ui) {
          var itemsOrder = _.chain($sortable.sortable('toArray')).where({
            'depth': 1
          }).pluck('item_id').map(function (i) {
            return 'status_id: ' + i;
          }).value();
          win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));
          win.booktype.sendToCurrentBook({
            'command': 'book_status_order',
            'order': itemsOrder
          }, function (data) {
            win.booktype.ui.notify();
          });

        });

        $sortable.nestedSortable({
          forcePlaceholderSize: true,
          handle: 'div',
          helper: 'clone',
          items: 'li.item',
          opacity: 0.6,
          placeholder: 'placeholder-status',
          revert: 250,
          tabSize: 25,
          tolerance: 'pointer',
          toleranceElement: '> div',
          maxLevels: 1,
          expandOnHover: 700,
          startCollapsed: true,
          protectRoot: true
        });

        // remove status
        $container.on('click', '.remove-status', function () {

          function _buildMessage($status) {
            var booktype = win.booktype;
            var msg = [booktype._('status_remove_confirmation')];
            var numChapters = $status.data('num-chapters');
            var numAttachments = $status.data('num-attachments');

            //add chapters warning if any
            if (numChapters > 0) {
              var _bold = _.sprintf("<b>%s</b>", numChapters)
              msg.push(_.sprintf(booktype._('status_remove__chapters'), { num_chapters: _bold }));
            }

            if (numChapters > 0 && numAttachments > 0)
              msg.push(booktype._('status_remove__and'));

            //add attachments warning if any
            if (numAttachments > 0) {
              var _bold = _.sprintf("<b>%s</b>", numAttachments)
              msg.push(_.sprintf(booktype._('status_remove__attachments'), { num_attachments: _bold }));
            }

            //if more than one element in array means chapters or attachments
            if (msg.length > 1)
              msg.push(booktype._('status_remove__suffix'));

            return msg.join(" ");
          }

          var $li = $(this).closest('li.item');
          win.booktype.utils.confirm({
            message: _buildMessage($li),
            width: 370,
          }, function (response) {
            if (!response) return;

            win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));
            win.booktype.sendToCurrentBook({
              'command': 'book_status_remove',
              'status_id': $li.attr('data-id')
            }, function (data) {
              win.booktype.ui.notify();

              if (data.result) {
                $li.remove();
                win.booktype.editor.data.statuses = data.statuses;
                win.booktype.utils.notification(win.booktype._("deleted_successfully"), "", {type: "success"});
              } else {
                win.booktype.utils.notification(data.message, "", {type: "error"});
              }
            });
          });
        });

        // edit status
        $container.on('click', '.edit-status', function () {
          var el = $(this);
          var statusName = el.closest('li.item').find('.status-name');
          var statusBlock = el.closest('li.item').find('.edit-status-block');

          statusName.hide();
          statusBlock.show();
          statusBlock.find('input').val(statusName.text());
          statusBlock.find('input').focus();
        });

        $container.on('click', '.edit-status-ok', function () {
          var $el = $(this),
            $input = $el.closest('.edit-status-block').find('input[type=text]'),
            $li = $el.closest('li.item'),
            statusName = $input.val();

          if (statusName) {
            $input.val('');
            win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));
            win.booktype.sendToCurrentBook({
              'command': 'book_status_rename',
              'status_name': statusName,
              'status_id': $li.attr('data-id')
            }, function (data) {
              win.booktype.ui.notify();
              $li.find('.status-name').text(statusName);
              $li.find('.status-name').show();
              $li.find('.edit-status-block').hide();

              win.booktype.editor.data.statuses = data.statuses;
            });
          }
        });
        $container.on('click', '.edit-status-cancel', function () {
          var $el = $(this),
            $li = $el.closest('li.item');

          $li.find('.status-name').text();
          $li.find('.status-name').show();
          $li.find('.edit-status-block').hide();
        });
        // add status
        $container.on('click', '.add-status', function () {
          var $el = $(this),
            $input = $el.closest('.input-group').find('input[type=text]'),
            statusName = $input.val(),
            template = _.template($('#status-item').html());

          if (statusName) {
            $input.val('');
            win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));
            win.booktype.sendToCurrentBook({
              'command': 'book_status_create',
              'status_name': statusName
            }, function (data) {
              $sortable.append(template({
                'name': statusName,
                'status_id': data.status_id
              }));
              win.booktype.ui.notify();

              win.booktype.editor.data.statuses = data.statuses;
            });
          }
        });
      });

      // Set a new license Link, when license combobox setting changes
      $('#inputLicense').change(function () {
        var licenseId = $(this).val();
        var licenseList = $('#license-link').data('licenses');

        if (licenseId in licenseList) {
          $('#license-link').attr('href', licenseList[licenseId]);
        }
      });

      $(document).on('click', '#insert_field', function () {
        var newFieldTmpl = _.template($('script.templateNewMetadataField').html());
        var fieldLabel = $('[name="new_field_name"]').val();
        var fieldName = $(this).data('meta-prefix') + '.' + win.booktype.utils.slugify(fieldLabel);

        var field = newFieldTmpl({
          'field_name': fieldName,
          'field_label': fieldLabel
        });

        // insert new field, clean field and close modal
        $('li.setting-controls').before(field);
        $('[name="new_field_name"]').val('');
        $('.modal.fade.in').modal('hide');

        var triggerBtn = $('[href="#appendField"]');
        var maxLimit = parseInt(triggerBtn.data('max-limit'), 10);
        if ($('textarea.meta-dynamic').length >= maxLimit)
          $(triggerBtn).addClass('hide');
      });

      $(document).on('click', 'ul.setting-list .meta_in_db.close', function () {
        var deleteModal = $('#deleteMetaFieldModal');
        var parent = $(this).closest('li');
        var toDelete = parent.find('input, textarea');
        deleteModal.data('to-delete', toDelete.attr('name'));

        deleteModal.modal('show');
      });

      // delete for metadata stuff (both standard and additional)
      $(document).on('click', '#confirm_delete', function () {
        var modal = $(this).closest('.modal.fade.in');
        var opts = {
          'command': modal.data('remote-cmd'),
          'toDelete': modal.data('to-delete'),
          'module': modal.data('reload-module')
        };

        win.booktype.sendToCurrentBook({
          'command': opts.command,
          'toDelete': opts.toDelete
        }, function (response) {
          if (response.result === true) {
            modal.data('to-delete', null);
            modal.modal('hide');

            // let's wait a little bit for modal to close
            // and avoid scroll problems
            setTimeout(function () {
              reloadModule(opts.module);
              win.booktype.ui.notify(win.booktype._('metafield_success_delete'));
            }, 500);
          } else {
            modal.modal('hide');
            win.booktype.ui.notify(win.booktype._('metafield_fail_delete'));
          }

          window.scrollTo(0, 0);
          setTimeout(function () {
            win.booktype.ui.notify();
          }, 2000);
        });
      });

      $(document).on('shown.bs.modal', '#appendField', function () {
        $('[name="new_field_name"]').focus();
      });

      $(document).on('keyup input', '[name="new_field_name"]', function () {
        if ($(this).val().length > 0) {
          $('#insert_field').prop('disabled', false);
        } else {
          $('#insert_field').prop('disabled', true);
        }
      });

      $(document).on('click', 'ul.setting-list .not_in_db.close', function () {
        // just remove focus effect
        $(this).blur();

        // remove field parent container
        var parent = $(this).closest('li');
        parent.slideUp('normal', function () {
          $(this).remove();

          // check remaining elements
          var maxLimit = parseInt($('[href="#appendField"]').data('max-limit'));
          if ($('textarea.meta-dynamic').length < maxLimit) {
            $('[href="#appendField"]').removeClass('hide');
          }
        });
      });

    };

    var reloadModule = function (option) {
      var clearMessages = false;
      router.loadSetting(option, clearMessages);
    };

    var createFlash = function (message, alert) {
      var flashTempl = _.template(
        $('script.templateFlashMessage').html()
      );
      return flashTempl({
        'message': message,
        'alert_type': alert
      });
    };

    var dismissFlash = function () {
      // fade out all alerts with bk-dismiss class.
      $('.bk-dismiss').each(function (i, alert) {
        var timeout = $(alert).data('dismiss-secs');
        setTimeout(function () {
          $(alert)
            .fadeOut(1000, 'linear')
            .remove();
        }, parseInt(timeout, 10) * 1000);
      });
    };

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'router': router,
      'name': 'settings'
    };
  })();

})(window, jQuery);
