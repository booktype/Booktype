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

(function (win, jquery, _) {
  'use strict';

	jquery.namespace('win.booktype.editor.publish');

  win.booktype.editor.publish = (function () {

    var removeTaskId = null;
    var settingsDialogFormat = null;

    var ExportModel = Backbone.Model.extend({
      defaults: {
          name: 'Export',
          taskID: '',
          files: {},
          comments: [],
          username: '',
          created: '',
          published: '',
          exported: ''
        }
      });

    var ExportView = Backbone.View.extend({
      tagName: 'div',
      className: 'export-item',

      events: {
        'click .dropdown-menu a.comment-on-export': 'doOpenComment',
        'click .dropdown-menu a.publish-export': 'doPublishExport',
        'click .dropdown-menu a.remove-export': 'doRemoveExport',
        'click .send-comment': 'doPostComment',
        'blur .export-name': 'doChangeName'
      },

      enableComments: function (state) {
        if (state) {
          this.$el.find('.send-comment').attr('aria-disabled', true).removeClass('disabled');
        } else {
          this.$el.find('.send-comment').attr('aria-disabled', true).addClass('disabled');
        }
      },

      doChangeName: function () {
        var $this = this;

        win.booktype.sendToCurrentBook({'command': 'rename_export_name',
          'task_id': $this.model.get('taskID'),
          'name': $this.$el.find('.export-name').text()},
          function () {
        });

      },

      doRemoveExport: function () {
        removeTaskId = this.model.get('taskID');

        jquery('#removeExportDialog').modal('show');
      },

      doPublishExport: function () {
        jquery('#publishDialog').modal('show');
      },

      doOpenComment: function () {
        this.$el.find('.export-comments .expand').closest('.export-comments').toggleClass('show');
      },

      doPostComment: function () {
        var $this = this;

        var content = $this.$el.find('textarea').val();

        win.booktype.ui.notify('Posting comment.');
        $this.enableComments(false);

        win.booktype.sendToCurrentBook({'command': 'post_export_comment',
          'task_id': $this.model.get('taskID'),
          'book_id': win.booktype.currentBookID,
          'content': content},
          function (data) {
            var comments = $this.model.get('comments');
            comments.push(data.comment);

            $this.model.set('comments', comments);
            $this.renderComments();

            $this.$el.find('textarea').val('');
            win.booktype.ui.notify();
            $this.enableComments(true);
          });
      },

      initialize: function () {
        this.template = _.template(jquery('#templatePublishLine').html());
        this.commentTemplate = _.template(jquery('#templatePublishComments').html());
      },

      renderComments: function () {
        var $comment = this.commentTemplate({'comments': this.model.get('comments')});
        this.$el.find('.export-comments .notification-list').html($comment);

        var num = this.model.get('comments').length;
        this.$el.find('.export-comments .badge').html(num);
      },

      remove: function () {
        var $this = this;

        this.$el.effect('clip', {}, 500, function () {
            $this.$el.remove();
          });
      },

      getFormatName: function (key) {
        return (jquery('.export-formats input[name="' + key + '"]').parent().text().trim() || key);
      },

      render: function () {
        var data = this.model.toJSON();
        data['getFormatName'] = this.getFormatName;

        this.$el.html(this.template(data));
        this.renderComments();

        return this;
      },

      destoryView: function () {
        this.undelegateEvents();
        this.$el.removeData().unbind();
        this.remove();
        Backbone.View.prototype.remove.call(this);
      }
    });


    var ExportListView = Backbone.View.extend({
      el: 'div.publish_history',

      initialize: function () {
        this.template = _.template(jquery('#templatePublishHistory').html());
        this.render();
        this.exportViewsList = {};
      },

      showProgress: function () {
        var $t = _.template(jquery('#templatePublishProgress').html());
        this.$el.find('.empty-message').remove();
        this.$el.prepend($t());
      },

      checkForEmpty: function () {
        if (this.collection.length === 0) {
          this.$el.append('<div class="empty-message">' + win.booktype._('export_list_empty', 'Nothing has been exported.') + '</div>');
        }
      },

      removeExport: function (taskID) {
        var view = this.exportViewsList[taskID];

        var elem = exportCollection.findWhere({'taskID': taskID});
        exportCollection.remove(elem);

        if (view) {
          view.remove();
        }

        this.checkForEmpty();
      },

      render: function () {
        var $this = this;

        $this.$el.empty();

        this.collection.each(function (expo) {
          var expoView = new ExportView({model: expo });
          expoView.render();
          // Not really needed
          expoView.$el.attr('data-task-id', expo.get('taskID'));

          this.exportViewsList[expo.get('taskID')] = expoView;

          $this.$el.append(expoView.$el);
        }, this);

        $this.checkForEmpty();

        $this.$el.find('.export-expand').click(function () {
            $(this).closest('.export-item').toggleClass('detail-view');
          });
        $this.$el.find('.export-comments .expand').click(function () {
            $(this).closest('.export-comments').toggleClass('show');
          });

        return this;
      },

      renderNew: function (expo) {
        var $this = this;
        var expoView = new ExportView({model: expo});

        expoView.render();
        expoView.$el.attr('data-task-id', expo.get('taskID'));

        this.exportViewsList[expo.get('taskID')] = expoView;

        $this.$el.find('.alert').remove();
        $this.$el.find('.empty-message').remove();

        $this.$el.prepend(expoView.$el);

        expoView.$el.find('.export-expand').click(function () {
            $(this).closest('.export-item').toggleClass('detail-view');
          });
        expoView.$el.find('.export-comments .expand').click(function () {
            $(this).closest('.export-comments').toggleClass('show');
          });

        return this;
      },

      destoryView: function () {
        _.each(this.exportViewsList, function (el) {
          if (el.destroyView) {
            el.destroyView();
          }
        });

        this.undelegateEvents();
        this.$el.removeData().unbind();
        this.remove();
        Backbone.View.prototype.remove.call(this);
      }
    });


    var getFormData = function ($dialog) {
      var settingsData = $dialog.find('form').serializeArray();

      $dialog.find('input[type=checkbox]:not(:checked)').each(function (idx, val) {
        settingsData.push({'name': jquery(val).attr('name'), 'value': 'off'});
      });

      return settingsData;
    };

    // A List of People
    var ExportCollection = Backbone.Collection.extend({
      model: ExportModel
    });

    var FilterView = Backbone.View.extend({
      el: '#publish-filter .publish-filter-container',
      events: {
        'click input[type=checkbox]': 'doCheckbox',
        'click button.btn-publish': 'doPublish',
        'click a.modal-open': 'doSettings'
      },

      initialize: function () {
        this.template = _.template(jquery('#templatePublishFilter').html());
        this.render();
        this.enableCheckboxes(true);
        this.enablePublish(false);
      },

      render: function () {
        this.$el.html(this.template({}));
      },

      enableCheckboxes: function (state) {
        if (state) {
          this.$el.find('input[type=checkbox]').removeAttr('disabled');
        } else {
          this.$el.find('input[type=checkbox]').prop('disabled', true);
        }
      },

      enablePublish: function (state) {
        if (state) {
          this.$el.find('button.btn-publish').attr('aria-disabled', true).removeClass('disabled');
        } else {
          this.$el.find('button.btn-publish').attr('aria-disabled', true).addClass('disabled');
        }
      },

      doSettings: function (evt) {
        var name = jquery(evt.target).parent().find('input').attr('name');

        if (_.isUndefined(name) || name === '') {
          return;
        }

        settingsDialogFormat = name;

        win.booktype.sendToCurrentBook({'command': 'export_settings_get',
          'book_id': win.booktype.currentBookID,
          'format': name},
          function (data) {
            var $dialog = jquery('#settings-' + settingsDialogFormat);
            var $form = $dialog.find('form');

            if (_.indexOf(['screenpdf', 'epub3', 'epub2', 'icml', 'docx', 'mobi', 'xhtml', 'pdfreactor-screenpdf'], settingsDialogFormat) !== -1) {
              $form.find('select[name=cover_image] option').slice(2).remove();

              _.each(data.covers, function (x, i) {
                var $a = jquery('<option value="' + i + '">' + x + '</option>');
                $form.find('select[name=cover_image]').append($a);
              });
            }

            _.each(data.settings, function (x) {
              var $field = jquery($form.get(0).elements[x.name]);

              if ($field.attr('type') === 'checkbox') {
                if (x.value === 'on') {
                  $field.prop('checked', true);
                } else {
                  $field.prop('checked', false);
                }
              } else {
                $field.val(x.value);
              }
            });
            $dialog.find('.steps').find('a').first().click();
            $dialog.modal('show');
          });


        return false;
      },

      doPublish: function () {
        var $this = this;

        win.booktype.ui.notify(win.booktype._('exporting_book', 'Exporting book'));
        showProgress();

        this.enablePublish(false);
        this.enableCheckboxes(false);

        var formats = jquery.map(this.$el.find('input[type=checkbox]:checked'), function (v) { return jquery(v).attr('name'); });

        win.booktype.sendToCurrentBook({'command': 'publish_book',
          'book_id': win.booktype.currentBookID,
          'formats': formats},
          function (data) {
            if (data.result === false) {
              console.log('Some kind of error during the publishing');
              if (data.reason) {
                // info popup
                var renderedModalInfoPopup = _.template(jquery('#modalInfoPopup').html())({
                  'header': win.booktype._('publish_error', 'Publish error'),
                  'body': data.reason
                });
                var modalInfoPopup = jquery(jquery.trim(renderedModalInfoPopup));
                modalInfoPopup.modal('show');
                $this.enablePublish(true);
                $this.enableCheckboxes(true);
                jquery('#content .publish_history .alert-warning').remove();
              }
            }
            win.booktype.ui.notify();
          });

      },

      doCheckbox: function () {
        if (this.$el.find('input[type=checkbox]:checked').length === 0) {
          this.enablePublish(false);
        } else {
          this.enablePublish(true);
        }
      },
      destoryView: function () {
        this.undelegateEvents();
        this.$el.removeData().unbind();
        this.remove();
        Backbone.View.prototype.remove.call(this);
      }
    });

    var PublishRouter = Backbone.Router.extend({
      routes: {
        'publish': 'publish'
      },

      publish: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['publish'];
          win.booktype.editor.data.activePanel.show();
        });
      }
    });

    var router = new PublishRouter();
    var filterView = null;
    var exportList = null;
    var exportCollection = null;

    var showProgress = function () {
      exportList.showProgress();
    };


    var dialogShown = function () {

    };

    /*******************************************************************************/
    /* SHOW                                                                        */
    /*******************************************************************************/

    var _show = function () {
      // set toolbar
      jquery('DIV.contentHeader').html(jquery('#templatePublishHeader').html());
      jquery('#content').html(jquery('#templatePublishContent').html());

      // Initialize everything
      exportCollection = new ExportCollection();

      filterView = new FilterView();
      exportList = new ExportListView({collection: exportCollection});

      // Show tooltips
      jquery('DIV.contentHeader [rel=tooltip]').tooltip({container: 'body'});

      // Remove exported file
      jquery('#removeExportDialog .btn-primary').on('click', function () {
        win.booktype.sendToCurrentBook({'command': 'remove_export',
          'task_id': removeTaskId},
          function (data) {
            if (data.result === true) {
              exportList.removeExport(removeTaskId);
            }

            jquery('#removeExportDialog').modal('hide');
          });
      });

      window.scrollTo(0, 0);

      jquery('div.settings-dialog').on('show.bs.modal', dialogShown);

      jquery('.wizard-settings').steps({
        startIndex: 0,
        headerTag: 'h3',
        bodyTag: 'section',
        transitionEffect: 'slideLeft',
        autoFocus: true,
        enableAllSteps: true,
        enableFinishButton: true,
        showFinishButtonAlways: true,

        onFinished: function () {
          var $dialog = jquery('#settings-' + settingsDialogFormat);
          var settingsData = getFormData($dialog);

          win.booktype.sendToCurrentBook({'command': 'export_settings_set',
            'format': settingsDialogFormat,
            'data': settingsData},
            function () {
              $dialog.modal('hide');
            });
        },
        labels: {
          next: win.booktype._('next', 'Next'),
          previous: win.booktype._('previous', 'Previous'),
          finish: win.booktype._('export_save', 'Save')
        }
      });

      win.booktype.sendToCurrentBook({'command': 'get_export_list',
        'book_id': win.booktype.currentBookID},
        function (data) {
          _.each(data.exports, function (elem) {
            if (!exportCollection) {
              return;
            }
            exportCollection.add(new ExportModel({
              name: elem.name,
              taskID: elem['task_id'],
              files: elem.files,
              comments: elem.comments,
              username: elem.username,
              created: elem.created})); //, {at: 0});
          });

          exportList.render();

        });

        win.booktype.sendToCurrentBook({
          'command': 'check_markers',
          'book_id': win.booktype.currentBookID
        }, function (data) {
          var info = $('div.book-info');
          var tmpl = null;

          info.empty();

          if (data.marked_chapters.length > 0) {
            tmpl = _.template($('#templateMarkedWarning').clone().html());
            info.append(tmpl());

            tmpl = _.template($('#templateMarkedChapters').clone().html());
            info.append(tmpl({'chapters': data.marked_chapters}));

            info.addClass('border-bottom');
          }
        });

      // Trigger events
      jquery(document).trigger('booktype-ui-panel-active', ['publish', this]);
    };

    /*******************************************************************************/
    /* HIDE                                                                        */
    /*******************************************************************************/

    var _hide = function (callback) {
      // Destroy tooltip
      jquery('DIV.contentHeader [rel=tooltip]').tooltip('destroy');

      //we should destroy settings panel steps/wizard
      jquery('.wizard-settings').steps('destroy');

      filterView.destoryView();
      exportList.destoryView();

      // Clear content
      jquery('#content').empty();
      jquery('DIV.contentHeader').empty();

      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    /*******************************************************************************/
    /* INIT                                                                        */
    /*******************************************************************************/

    var _init = function () {
      jquery('#button-publish').on('click', function () { Backbone.history.navigate('publish', true); });

      win.booktype.subscribeToChannel('/booktype/book/' + win.booktype.currentBookID + '/' + win.booktype.currentVersion + '/',
        function (message) {
          var funcs = {
            'remove_export': function () {
              if (exportList) {
                exportList.removeExport(message['task_id']);
              }
            },

            'new_export_comment': function () {
              if (!exportCollection) {
                return;
              }
              var elem = exportCollection.findWhere({'taskID': message['task_id']});
              var comments = elem.get('comments');

              comments.push({'username': message.username,
                  'email': message.email,
                  'created': message.created,
                  'content': message.content});
              elem.set('comments', comments);

              if (exportList) {
                exportList.exportViewsList[message['task_id']].renderComments();
              }
            },

            'rename_export_name': function () {
              if (!exportCollection) {
                return;
              }
              var elem = exportCollection.findWhere({'taskID': message['task_id']});
              elem.set('name', message.name);

              if (exportList) {
                exportList.exportViewsList[message['task_id']].render();
              }
            },

            'book_published': function () {
              if (message.state === 'SUCCESS') {
                jquery('#content .publish_history .publishing-message').fadeOut().remove();

                var newExport = new ExportModel({name: message.name,
                  taskID: message['task_id'],
                  files: message.files,
                  comments: message.comments,
                  username: message.username,
                  created: message.created});

                if (exportCollection) {
                  exportCollection.add(newExport, {at: 0});
                }

                if (exportList) {
                  exportList.renderNew(newExport);
                }

                if (filterView) {
                  filterView.enableCheckboxes(true);

                  if (jquery('#content input[type=checkbox]:checked').length !== 0) {
                    filterView.enablePublish(true);
                  }
                }
              }
            }
          };

          if (funcs[message.command]) {
            funcs[message.command]();
          }
        }
      );

    };

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'name': 'publish'
    };
  })();

})(window, jQuery, _);
