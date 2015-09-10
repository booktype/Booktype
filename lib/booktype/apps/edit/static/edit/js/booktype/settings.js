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
            var getTempl = win.booktype.ui.getTemplate;
            var notAvailable = '';

            if (response.status === 403)
              notAvailable = getTempl('templatePermissionDenied')
            else
              notAvailable = getTempl('templateModuleNotAvailable');

            $('#setting_content').html(notAvailable)
          })
          .done(function (html) {
            if (clearMessages === true)
              $('#setting_content').siblings('.alert').remove();

            $('#setting_content').html(html);
            $('#setting_content').trigger(module + '-loaded');
          })
          .always(function(){
            if (clearMessages === true)
              win.booktype.ui.notify();
          });
      }
    });

    var router = new SettingsRouter();

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
      $('#content').empty();
      $('#content').removeClass('settings');
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

            if (resp.error) {
              if (resp.data !== undefined) {
                $('#setting_content').empty().html(resp.data);
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

            var $container = $('#setting_content');
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
          if (!window.confirm(win.booktype._('chapter_status_remove_confirmation', 'Do you really want to delete this Chapter Status?'))) {
            return;
          }

          var $li = $(this).closest('li.item');
          win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));
          win.booktype.sendToCurrentBook({
            'command': 'book_status_remove',
            'status_id': $li.attr('data-id')
          }, function (data) {
            $li.remove();
            win.booktype.ui.notify();
            win.booktype.editor.data.statuses = data.statuses;
          });
        });
        // edit status
        $container.on('click', '.edit-status', function () {
          var el = $(this);
          var statusname = el.closest('li.item').find('.status-name').text();
          el.closest('li.item').find('.status-name').hide();
          el.closest('li.item').find('.edit-status-block').show();
          el.closest('li.item').find('.edit-status-block').find('input').val(statusname);
          el.closest('li.item').find('.edit-status-block').find('input').focus();
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
      $(document).on('change', 'SELECT[name=license]', function () {
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
        var maxLimit = parseInt(triggerBtn.data('max-limit'));
        if ($('textarea.meta-dynamic').length >= maxLimit)
          $(triggerBtn).addClass('hide');
      });

      $(document).on('click', 'ul.setting-list .meta_in_db.close', function () {
        var deleteModal = $('#deleteMetaFieldModal');
        var toDelete = $(this).closest('li').find('textarea.meta-dynamic');
        deleteModal.data('to-delete', toDelete.attr('name'));

        deleteModal.modal('show');
      });

      $(document).on('click', '#confirm_delete', function () {
        var modal = $(this).closest('.modal.fade.in');
        var toDelete = modal.data('to-delete');

        win.booktype.sendToCurrentBook({
          'command': 'remove_metafield',
          'toDelete': toDelete,
        }, function (response) {
          if (response.result === true) {
            modal.data('to-delete', null);
            modal.modal('hide');

            // let's wait a little bit for modal to close
            // and avoid scroll problems
            setTimeout(function () {
              reloadModule('additional-metadata');
              win.booktype.ui.notify(win.booktype._('metafield_success_delete'));
            }, 500);
          } else {
            modal.modal('hide');
            win.booktype.ui.notify(win.booktype._('metafield_fail_delete'));
          }

          window.scrollTo(0, 0);
          setTimeout(function() {
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

      // ----- Roles -----
      $(document).on('mouseenter', '.roles .list li', function () {
        $(this).addClass('show-remove-btn');
      });

      $(document).on('mouseleave', '.roles .list li', function () {
        $(this).removeClass('show-remove-btn');
      });

      // toggle description show and hide
      $(document).on('click', '.toggle-description a', function () {
        $(this).closest('.box').find('.role-description').toggleClass('show');
      });

      // click on a user activates options
      $(document).on('click', '#assignUsers .users-list .list li', function () {
        $(this).parent().children().removeClass('active');
        $(this).toggleClass('active');

        var username = $(this).find('p').html(),
          userRoles = $(this).data('user-roles'),
          roles = $(this).closest('.modal-body').find('.assign-options .roles-options button');

        $(this).closest('.modal-body').find('.assign-options .user-roles span').empty().append(username);

        // reset roles buttons
        $(roles).removeClass('btn-success disabled-tooltip active');
        $(roles).addClass('btn-default');

        // for each role, check if already enable for that user
        $.each(roles, function (_i, role) {
          // remove tooltip for disabled buttons
          unWrapDisabledRole(role);

          var roleId = parseInt($(role).data('role-id'), 10);
          if ($.inArray(roleId, userRoles) === -1) {
            $(role).removeClass('disabled');
          } else {
            $(role)
              .removeClass('btn-default')
              .addClass('disabled-tooltip btn-success disabled');

            wrapDisabledRole(role);
            enableModalTooltips();
          }
        });
      });

      $(document).on('click', '.assign-options .roles-options .btn', function () {
        $(this).closest('.modal-content').find('#assign').removeClass('disabled');
      });

      // reset everything on modal hide
      $(document).on('hidden.bs.modal', '#assignUsers', function () {
        $('.users-list .list li').removeClass('active');
        $('.assign-options .roles-options button').addClass('disabled').removeClass('active');
        $('.assign-options .user-roles span').empty();
        $('#assign').addClass('disabled');
      });

      // calculate the height and apply to user list
      $(document).on('shown.bs.modal', '#assignUsers', function () {
        var optionsHeight = $(this).find('.assign-options').outerHeight();
        $(this).find('.users-list').css('bottom', optionsHeight);

        enableModalTooltips();
      });

      // patching for caise insensitive on jquery contains
      $.expr[':'].contains = $.expr.createPseudo(function (arg) {
        return function (elem) {
          return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
        };
      });

      // we need an inline search for user in assign roles
      $(document).on('keyup', '.search-box input', function () {
        var value = $(this).val();

        $('.users-list > ul > li:not(:contains(' + value + '))').hide();
        $('.users-list > ul > li:contains(' + value + ')').show();
      });

      $(document).on('click', '.search-box .btn', function () {
        $('.search-box input').trigger('keyup');
      });

      // assign user to role
      $(document).on('click', '#assign', function () {
        win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));
        var user = $('.users-list > ul > li.active:first').data('user-id'),
          roles = $('.role-btn.active').not('.disabled');

        var rolesid = $.map(roles, function (elem) {
          var roleID = $(elem).data('role-id');
          if (typeof roleID === 'number') {
            return roleID;
          }
        });

        win.booktype.sendToCurrentBook({
            'command': 'assign_to_role',
            'userid': user,
            'roles': rolesid
          },
          function () {
            win.booktype.ui.notify();
            $('#assignUsers').modal('hide');
            Backbone.history.loadUrl('settings/roles');
          }
        );
      });

      // remove user from role
      $(document).on('click', '.remove-btn button', function () {
        var self = this,
          userID = $(this).data('user-id'),
          bookRoleID = $(this).data('bookrole-id'),
          roleID = $(this).data('role-id');


        win.booktype.ui.notify(win.booktype._('sending_data', 'Sending data.'));

        win.booktype.sendToCurrentBook({
            'command': 'remove_user_from_role',
            'userid': userID,
            'roleid': bookRoleID
          },
          function (data) {
            win.booktype.ui.notify();
            if (data.result) {
              $(self).closest('li').remove();
              var userToAssign = $('#assignUsers ul li[data-user-id="' + userID + '"]');
              var newRolesIDS = userToAssign.data('user-roles').filter(function (id) {
                return id !== roleID;
              });
              console.log(newRolesIDS, roleID);
              userToAssign.data('user-roles', newRolesIDS);
            } else {
              win.booktype.ui.notify(win.booktype._('sending_data'));
            }
          }
        );
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

    var enableModalTooltips = function () {
      $('[rel=tooltip]').tooltip({
        container: 'body'
      });
    };

    var wrapDisabledRole = function (roleBtn) {
      var tooltip = win.booktype._('already_in_role', 'Selected user already belongs to this role');
      $(roleBtn).wrap(function () {
        return '<div rel="tooltip" style="display: inline-block" data-placement="top" data-original-title="' + tooltip + '"></div>';
      });
    };

    var unWrapDisabledRole = function (roleBtn) {
      if ($(roleBtn).parent().is('div[rel=tooltip]')) {
        $(roleBtn).unwrap();
      }
    };

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'router': router,
      'name': 'settings',
    };
  })();

})(window, jQuery);