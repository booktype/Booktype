(function (win, $) {
  'use strict';

  $.namespace('win.booktype.editor.settings');

  win.booktype.editor.settings = (function () {

    var SettingsRouter = Backbone.Router.extend({
      routes: {
        'settings': 'settings',
        'settings/roles': 'roles',
        'settings/:module': 'loadSetting'
      },

      settings: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['settings'];
          win.booktype.editor.data.activePanel.show();
        });
      },

      roles: function () {
        if (win.booktype.editor.settings.uiLoaded === undefined) {
          this.settings();
        }

        var $settings = $('#setting_content');
        var users = {};
        var roles = {};

        $settings.html('');

        win.booktype.ui.notify('Loading section');

        var _loadUsers = function () {
          $.get(win.booktype.baseURL + '/_api/books/' + win.booktype.currentBookID + '/users/')
            .fail(function (response) {
              _settingsLoadFailHandler(response);
            })
            .done(function (response) {
               // no users handler
              if (!response.results.length) {
                $settings.html($('script.templateRolesNoUsers').html());
                return;
              }

              _.each(response.results, function (user) {
                users[user.id] = user;
              });

              var tableTemplate = _.template($('script.templateRolesTable').html());
              var rowTemplate = _.template($('script.templateRolesTableRow').html());
              var rowsRednered = '';
              var roleButtonsRendered = '';
              var permissionSpansRendered = '';

              // create rows
              _.each(users, function (user) {
                // create roles and permissions in popover
                roleButtonsRendered = '';

                _.each(user.book_roles, function (bookRole) {
                  permissionSpansRendered = '';

                  // ignore default roles
                  if (bookRole.role.name === 'anonymous_users' || bookRole.role.name === 'registered_users'){
                    return
                  }

                  _.each(bookRole.role.permissions, function (permission) {
                    var permissionSpan = document.createElement('span');
                    permissionSpan.setAttribute('class', 'label label-info');
                    permissionSpan.innerHTML = permission.description;
                    permissionSpansRendered += permissionSpan.outerHTML;
                  });

                  var roleButton = document.createElement('a');
                  roleButton.setAttribute('class', 'btn btn-sm btn-default book-roles');
                  roleButton.setAttribute('role', 'button');
                  roleButton.setAttribute('data-html', 'true');
                  roleButton.setAttribute('data-placement', 'right');
                  roleButton.setAttribute('data-trigger', 'focus');
                  roleButton.setAttribute('tabindex', '0');
                  roleButton.setAttribute('title', bookRole.role.description);
                  roleButton.setAttribute('data-content', permissionSpansRendered);
                  roleButton.innerHTML = bookRole.role.name;
                  roleButtonsRendered += roleButton.outerHTML;
                });

                rowsRednered += rowTemplate({
                  'profile_image_url': user.profile_image_url,
                  'profile_url': user.profile_url,
                  'username': user.username,
                  'get_full_name': user.get_full_name,
                  'user_id': user.id,
                  'book_roles': roleButtonsRendered
                });
              });

              // render table with rows
              $settings.html(
                tableTemplate({'rows': rowsRednered})
              );

              // init popovers
              if (window.booktype.editor.settingsRolesShowPermissions) {
                $('.book-roles').popover();
              }

              // load all system roles
              _loadRoles();

            })
            .always(function () {
              win.booktype.ui.notify();
            });
        };

        var _loadRoles = function () {
          $.get(win.booktype.baseURL + '/_api/roles/')
            .fail(function (response) {
              _settingsLoadFailHandler(response);
            })
            .done(function (response) {
              var changeRolesModal = $('#changeRoles');
              var changeRolesModalUsername = $('h3 span', changeRolesModal);

              _.each(response.results, function (role) {
                roles[role.id] = role;
              });

              // change role button
              $('button[href="#changeRoles"]').on('click', function () {
                var userID = $(this).attr('data-user-id');
                var user = users[userID];
                var roleButtonsRendered = '';
                var $changeRoleButton = $('#saveChangeRole');

                changeRolesModalUsername.append(user.username);

                // create roles buttons
                _.each(roles, function (role) {
                  var permissionSpansRendered = '';

                  // ignore default roles
                  if (role.name === 'anonymous_users' || role.name === 'registered_users') {
                    return
                  }

                  _.each(role.permissions, function (permission) {
                    var permissionSpan = document.createElement('span');
                    permissionSpan.setAttribute('class', 'label label-info');
                    permissionSpan.innerHTML = permission.description;
                    permissionSpansRendered += permissionSpan.outerHTML;
                  });

                  var roleButton = document.createElement('button');
                  roleButton.setAttribute('class', 'btn btn-default role-btn');
                  roleButton.setAttribute('data-toggle', 'button');
                  roleButton.setAttribute('data-role-id', role.id);
                  roleButton.setAttribute('title', role.description);
                  roleButton.setAttribute('data-content', permissionSpansRendered);
                  roleButton.innerHTML = role.name;

                  _.each(user.book_roles, function (user_role) {
                    if (user_role.role.id === role.id) {
                      $(roleButton).addClass('active');
                    }
                  });

                  roleButtonsRendered += roleButton.outerHTML;
                });

                // insert roles into modal
                $('.roles-options', changeRolesModal).html(roleButtonsRendered);

                $('.role-btn', changeRolesModal).on('click', function () {
                  setTimeout(function () {
                    if ($('.role-btn.active', changeRolesModal).length === 0) {
                      $changeRoleButton.removeClass('btn-primary');
                      $changeRoleButton.addClass('btn-danger');
                      $changeRoleButton.text(win.booktype._('remove_user_from_the_book', 'Remove user from the book'));
                    } else {
                      $changeRoleButton.removeClass('btn-danger');
                      $changeRoleButton.addClass('btn-primary');
                      $changeRoleButton.text(win.booktype._('save', 'Save'));
                    }
                  }, 50);

                  $changeRoleButton.removeClass('disabled');
                });

                if (window.booktype.editor.settingsRolesShowPermissions) {
                  // init custom popover
                  $('button', changeRolesModal).popover({
                    html: true,
                    trigger: 'manual',
                    placement: 'bottom'
                  }).on("mouseenter", function () {
                    var _this = this;
                    $(this).popover("show");
                    $(this).siblings(".popover").on("mouseleave", function () {
                      $(_this).popover('hide');
                    });
                  }).on("mouseleave", function () {
                    var _this = this;
                    setTimeout(function () {
                      if (!$(".popover:hover").length) {
                        $(_this).popover("hide")
                      }
                    }, 10);
                  });
                }

                // save button handler
                $changeRoleButton.on('click', function () {
                  var selectedRoles = [];
                  var rolesToAssign = [];
                  var rolesToRemove = [];
                  var userRolesID = _.map(user.book_roles, function (book_role) {
                    return book_role.role.id;
                  });
                  var assignXHRisDone = false;
                  var removeXHRisDone = false;
                  var reloadRequired = false;

                  $('.roles-options button.active', changeRolesModal).each(function () {
                    selectedRoles.push(parseInt($(this).attr('data-role-id')));
                  });

                  _.each(userRolesID, function (roleID) {
                    if (!_.contains(selectedRoles, roleID)) {
                      rolesToRemove.push(roleID);
                    }
                  });

                  _.each(selectedRoles, function (selectedRole) {
                    if (!_.contains(userRolesID, selectedRole)) {
                      rolesToAssign.push(selectedRole);
                    }
                  });

                  // assign roles
                  if (rolesToAssign.length) {
                    $.post(
                      win.booktype.baseURL + '/_api/books/' + win.booktype.currentBookID + '/grant-user/multi/',
                      {
                        'role_names': _.map(rolesToAssign, function (id) {
                          return roles[id].name
                        }),
                        'user_id': userID
                      }
                    ).done(function () {
                      reloadRequired = true;
                    }).fail(function (response) {
                      alert(win.booktype._('access_denied', 'Access denied.'));
                    }).always(function () {
                      assignXHRisDone = true;
                    });
                  } else {
                    assignXHRisDone = true;
                  }

                  // remove roles
                  if (rolesToRemove.length) {
                    $.post(
                      win.booktype.baseURL + '/_api/books/' + win.booktype.currentBookID + '/remove-grant-user/multi/',
                      {
                        'role_names': _.map(rolesToRemove, function (id) {
                          return roles[id].name
                        }),
                        'user_id': userID
                      }
                    ).done(function () {
                      reloadRequired = true;
                    }).fail(function (response) {
                      alert(win.booktype._('access_denied', 'Access denied.'));
                    }).always(function () {
                      removeXHRisDone = true;
                    });

                  } else {
                    removeXHRisDone = true;
                  }

                  // a little bit redundant, but it will improve feeling
                  var interval = setInterval(function () {
                    if (assignXHRisDone && removeXHRisDone) {
                      clearInterval(interval);
                      $('#changeRoles').modal('hide');

                      if (reloadRequired) {
                        Backbone.history.loadUrl('settings/roles');
                      }
                    }
                  }, 100);

                });

                // show modal
                changeRolesModal.modal('show');
              });

              // reset everything on modal hide
              $(document).on('hidden.bs.modal', '#changeRoles', function () {
                var $changeRoleButton = $('#saveChangeRole');
                changeRolesModalUsername.html('');
                $('.roles-options', changeRolesModal).html('');
                $changeRoleButton.unbind('click');
                $changeRoleButton.addClass('disabled');
                $changeRoleButton.removeClass('btn-danger');
                $changeRoleButton.addClass('btn-primary');
                $changeRoleButton.text(win.booktype._('save', 'Save'));
              });

            })
            .always(function () {
              win.booktype.ui.notify();
            });
        };

        // load users with roles/permissions inside
        _loadUsers();

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