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

  jquery.namespace('win.booktype.editor.edit');

  win.booktype.editor.edit = (function () {
    var chapterID = null,
      saveState = null,
      _actions = {},
      isZenMode = false,
      tabs = [],
      showImagePopup = false;

    var _loadChapterHistory = function () {
      win.booktype.sendToCurrentBook({
        'command': 'get_chapter_history',
        'chapter': chapterID
      }, function (dta) {

        jquery('#history-tab-list').html('');

        var restoreLabel = win.booktype._('restore', 'RESTORE');
        var $t = _.template(jquery('#templateChapterRevision').html());

        jquery.each(dta.history, function (n, item) {
          item.active = false;
          item.label = restoreLabel;
          item.current_username = win.booktype.username;
          jquery('#history-tab-list').append($t(item));
        });

        // gets diff with current unsaved content
        // Sends unsaved content to the diff
        var $editor = Aloha.getEditableById('contenteditor');

        if (!_.isUndefined($editor) && $editor && $editor.isModified()) {
          var maxRevision = jquery('#history-tab-list button').first()[0].dataset.revision;
          win.booktype.ui.notify(win.booktype._('loading_data', 'Loading data.'));

          win.booktype.sendToCurrentBook({
            'command': 'chapter_diff',
            'chapter': chapterID,
            'revision1': maxRevision,
            'revision2': maxRevision,
            'content': $editor.getContents()
          }, function (datum) {
            jquery('#contentrevision').html(datum.output);
            win.booktype.ui.notify();
            Aloha.trigger('editor.chapter_history.chapter_diff', {});
          });
        }

        jquery('#history-tab-list li').click(function () {
          // hide active restore btn and item
          jquery('#history-tab-list div.restore-btn').hide();
          jquery('#history-tab-list li').removeClass('active');

          // now activate current clicked elem
          jquery(this).find('div.restore-btn').show();
          jquery(this).addClass('active');

          var maxRevision = jquery('#history-tab-list span.revision-number').first().data('revision');
          var selectedRevision = jquery(this).find('span.revision-number').data('revision');

          win.booktype.ui.notify(win.booktype._('loading_data', 'Loading data.'));
          var currentContent = null;

          if (maxRevision === selectedRevision){
            currentContent = Aloha.getEditableById('contenteditor').getContents();
          }
          win.booktype.sendToCurrentBook({
            'command': 'chapter_diff',
            'chapter': chapterID,
            'revision1': selectedRevision,
            'revision2': maxRevision,
            'content': currentContent
          }, function (datum) {
            jquery('#contentrevision').html(datum.output);
            win.booktype.ui.notify();
            Aloha.trigger('editor.chapter_history.chapter_diff', {});
          });
        });

        jquery('#history-tab-list button').click(function () {
          var _this = this;
          _checkIfModified(function(){
            win.booktype.sendToCurrentBook({
              'command': 'revert_revision',
              'chapter': chapterID,
              'revision': _this.dataset.revision
            }, function (datum) {
              if (datum.status && datum.result) {
                //reload editor and notify
                disableRevisionHistoryBlock();
                win.booktype.ui.notify(win.booktype._('revision_reverted', 'Revision reverted'));
                var $editor = Aloha.getEditableById('contenteditor');
                $editor.setUnmodified();
                win.booktype.editor.editChapter(chapterID, true);
                _loadChapterHistory();

                Aloha.trigger('editor.chapter_history.revert_revision', {});

              } else {
                win.booktype.ui.notify(win.booktype._('revert_revision_error', 'Revision revert failed'));
              }
            });
          });
        });

        // to enable first one by default
        jquery('#history-tab-list li:first').click();

        Aloha.trigger('editor.chapter_history.history_loaded', {});
      });
    };

    var disableSave = function (state) {
      if (state === saveState) return;

      jquery('#button-save').prop('disabled', state);
      jquery('#button-save-toggle').prop('disabled', state);

      saveState = state;
    };

    // enable/disable block for displaying revisions diff
    var enableRevisionHistoryBlock = function () {
      if (!jquery('#contentrevision').length) {
        var revisionHistoryBlock = jquery('<div>').attr({
          id: 'contentrevision'
        });
        revisionHistoryBlock.html(Aloha.getEditableById('contenteditor').getContents());
        jquery('#content').prepend(revisionHistoryBlock);
      } else {
        throw new Error('#contentrevision block already exists');
      }
      jquery('#content .templateAlohaContent').hide();

      // switch off image popup
      if (jquery('#imagePopup').is(':visible')) {
        jquery('#imagePopup').hide();
        showImagePopup = true;
      } else {
        showImagePopup = false;
      }
    };

    var disableRevisionHistoryBlock = function () {
      if (jquery('#contentrevision').length) {
        jquery('#contentrevision').remove();
      } else {
        throw new Error('#contentrevision block does not exists');
      }
      /// some more code here
      jquery('#content .templateAlohaContent').show();

      // switch on image popup
      if (showImagePopup) jquery('#imagePopup').show();
    };

    //enable disable editor functions
    var enableEditor = function () {
      if (jquery('#contenteditor').attr('contenteditable') !== 'true') {
        jquery('#contenteditor').attr({'contenteditable': true});
        Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});
        // Enable editor menus and toolbars
        disableSave(false);
        jquery('.contentHeader button.dropdown-toggle').removeClass('disabled');
        jquery('.color-picker-item > button').removeClass('disabled');
        jquery('.contentHeader button.action').each(function (idx, elem) {
          if (!_actions[jquery(elem).prop('class')]) {
            jquery(elem).removeClass('disabled');
          }
        });
      }
    };

    var disableEditor = function () {
      if (jquery('#contenteditor').attr('contenteditable') === 'true'){
        jquery('#contenteditor').attr({'contenteditable': false});
        // Disable editor menus and toolbars
        disableSave(true);
        jquery('.contentHeader button.dropdown-toggle').addClass('disabled');
        jquery('.color-picker-item > button').addClass('disabled');
        jquery('.contentHeader button.action').each(function (idx, elem) {
          _actions[jquery(elem).prop('class')] = jquery(elem).hasClass('disabled');
          jquery(elem).addClass('disabled');
        });
      }
    };

    var saveContent = function (params) {
      params = params || {minor: false};
      var content = Aloha.getEditableById('contenteditor').getContents();

      win.booktype.ui.notify(win.booktype._('saving_chapter', 'Saving chapter.'));

      disableSave(true);

      win.booktype.sendToCurrentBook({
        'command': 'chapter_save',
        'chapterID': chapterID,
        'content': content,
        'continue': true,
        'comment': params.comment || '',
        'author': '',
        'authorcomment': '',
        'minor': params.minor
      },
        function (data) {
          win.booktype.ui.notify();

          // Set content as unmodified after the save
          Aloha.getEditableById('contenteditor').setUnmodified();

          if (!_.isUndefined(params.callback)) {
            params.callback();
          }

          var doc = win.booktype.editor.getChapterWithID(chapterID);
          jquery(document).trigger('booktype-document-saved', [doc]);
        }
      );
    };

    var _masterCallback = [];

    var _checkIfModified = function (callback, errback) {
      var $editor = Aloha.getEditableById('contenteditor');

      if (!_.isUndefined($editor) && $editor && $editor.isModified()) {
        var $dialog = jquery('#contentModifiedModal');

        $dialog.modal('show');
        _masterCallback.push(callback);

        return true;
      }

      callback();
      return true;
    };

    var _show = function () {
      jquery('#button-toc').addClass('active');

      var t = win.booktype.ui.getTemplate('templateAlohaToolbar');
      var t2 = _.template(jquery('#templateAlohaFull').html());

      saveState = null;

      // Disable active options
      jquery('#button-toc').parent().removeClass('active');

      jquery('DIV.contentHeader').html(t);
      jquery('DIV.contentHeader [rel=tooltip]').tooltip({container: 'body'});
      jquery('DIV.contentHeader').append(t2());


      jquery('a.zenBtn').click(function (e) {
        jquery('body').toggleClass('zenMode');
        isZenMode = jquery('body').hasClass('zenMode');

        // Hide all possible open tabs
        jquery('section.tab-content').hide();
        jquery('.right-tabpane').removeClass('open hold');
        jquery('.right-tablist li').removeClass('active');
        jquery('.left-tabpane').removeClass('open hold');
        jquery('.left-tablist li').removeClass('active');

        return false;
      });

      var t2 = win.booktype.ui.getTemplate('templateAlohaContent');
      jquery('#content').html(t2);

      // update direction and language attributes
      var alohaContenteditor = Aloha.jQuery('#contenteditor');
      alohaContenteditor.attr('dir', window.booktype.bookDir);
      alohaContenteditor.attr('lang', window.booktype.bookLang);
      alohaContenteditor.aloha();

      // HIDE
      jquery('#right-tabpane section[source_id=hold-tab]').hide();
      jquery('#hold-tab').hide();

      var _triggerBeforeClose = function () {
        var chapterID = booktype.editor.getCurrentChapterID();
        var currentChapterItem = booktype.editor.getChapterWithID(chapterID);

        // trigger event
        jquery(document).trigger('booktype-editor-before-close', [currentChapterItem])
      }

      // Cancel editing
      jquery('#button-cancel').on('click', function () {
        // let's trigger closing editor to be able to attach actions
        _triggerBeforeClose();

        Backbone.history.navigate('toc', true);
        jquery('#button-toc').parent().addClass('active');

        // NOTE: shall we trigger after close event? let's do it when needed
        return false;
      });

      // Save chapter
      jquery('#button-save').on('click', function () { win.booktype.editor.edit.saveContent(); });

      jquery('#button-save-with-comment').on('click', function () {
        jquery('#saveContentWithCommentModal').modal('show');
      });

      jquery('#saveContentWithCommentModal').on('shown.bs.modal', function () {
        jquery('#saveContentWithCommentModal textarea[name=comment]').focus();
      });

      jquery('#button-save-minor-change').on('click', function () { win.booktype.editor.edit.saveContent({minor: true}); });

      jquery('#button-save-and-close').on('click', function () {
        win.booktype.editor.edit.saveContent({callback: function () {
          // let's trigger closing editor to be able to attach actions
          _triggerBeforeClose();

          Backbone.history.navigate('toc', true);
          jquery('#button-toc').parent().addClass('active');
        }});
      });

      // Autosave chapter
      if (win.booktype.editor.autosave.enabled) {
        setInterval(function () {
          var $editor = Aloha.getEditableById('contenteditor');
          if (!_.isUndefined($editor) && $editor && $editor.isModified()) {
            win.booktype.editor.edit.saveContent({minor: true})
          }
        }, win.booktype.editor.autosave.delay * 1000);
      }

      // Tabs
      tabs = [];

      if (win.booktype.editor.isEnabledTab('edit', 'chapters')) {
        var t1 = win.booktype.editor.createLeftTab('chapters-tab', 'big-icon-chapters', win.booktype._('chapters', 'Chapters')),
          $panel = jquery('SECTION[source_id=chapters-tab]');

        // Expand TOC
        jquery('BUTTON[rel=tooltip]', $panel).on('click', function () {
          jquery('BUTTON[rel=tooltip]', $panel).tooltip('destroy');
          // TODO
          // Must check if this content has been edited
          Backbone.history.navigate('toc', true);
        });

        t1.isOnTop = true;
        t1.onActivate = function () {
          jquery('BUTTON[rel=tooltip]', $panel).tooltip({container: 'body'});

          var _draw = function () {
            jquery('UL.edit-toc', $panel).empty();

            jquery.each(win.booktype.editor.data.chapters.chapters, function (i, chap) {
              if (chap.attributes.isSection) {
                jquery('UL.edit-toc', $panel).append(jquery('<li><div><span class="section">' + chap.get('title') + '</span></div></li>'));
              } else {
                var $l = jquery('<a href="#"/>').text(chap.get('title'));

                $l.on('click', function () {
                  win.booktype.editor.editChapter(chap.get('chapterID'));
                  return false;
                });

                var $a = jquery('<li/>').wrapInner('<div/>').wrapInner($l);
                if (win.booktype.editor.getCurrentChapterID() === chap.get('chapterID')) {
                  jquery('LI', $a).addClass('active');
                }
                jquery('UL.edit-toc', $panel).append($a);
              }
            });
          };

          _draw();

          this._tc = function () {
            _draw();
          };

          win.booktype.editor.data.chapters.on('modified', this._tc);
          return false;
        };

        t1.onDeactivate = function () {
          if (this._tc) {
            win.booktype.editor.data.chapters.off('modified', this._tc);
            this._tc = null;
          }

          jquery('BUTTON[rel=tooltip]', $panel).tooltip('destroy');
        };

        tabs.push(t1);
      }

      if (win.booktype.editor.isEnabledTab('edit', 'attachments')) {
        var t2 = win.booktype.editor.createRightTab('attachments-tab', 'big-icon-attachments', win.booktype._('attachments', 'Attachments'));
        t2.onActivate = function () { };
        tabs.push(t2);
      }

      if (win.booktype.editor.isEnabledTab('edit', 'history')) {
        var t4 = win.booktype.editor.createRightTab('history-tab', 'big-icon-history', win.booktype._('chapter_history', 'Chapter History'));
        t4.onActivate = function () {
          disableEditor();
          enableRevisionHistoryBlock();
          _loadChapterHistory();
        };

        t4.onDeactivate = function () {
          disableRevisionHistoryBlock();
          enableEditor();
        };

        tabs.push(t4);
      }

      if (win.booktype.editor.isEnabledTab('edit', 'style')) {
        var t5 = win.booktype.editor.createLeftTab('style-tab', 'big-icon-style', win.booktype._('choose_your_design', 'Choose Your Design'));

        var $container = jquery('section[source_id=style-tab]');

        if (!_.isUndefined(win.booktype.editor.themes)) {
          win.booktype.editor.themes.initPanel($container);
        }

        t5.onActivate = function () {
          if (!_.isUndefined(win.booktype.editor.themes)) {
            win.booktype.editor.themes.activatePanel();
          }
        };

        tabs.push(t5);
      }

      // ICEJS TAB
      if (win.booktype.editor.isEnabledTab('edit', 'icejs') &&
          jquery('#create-ice-tab').data('has-perm') &&
          Aloha.settings.plugins.icejs.enabled)
        {
        var iceTab = win.booktype.editor.createRightTab('icejs-tab', 'big-icon-track', win.booktype._('tracking_options', 'Tracking Options'));

        // according to tracking state, change buttons state
        var checkBtnState = function () {
          var buttons = jquery('.tracking-action-buttons button:not(.single-change)');
          if (typeof(win.booktype.tracker) !== 'undefined') {
            buttons.prop('disabled', !win.booktype.tracker.isTracking);
          } else {
            buttons.prop('disabled', true);
          }
        };

        // binding events
        jquery(document).on('click', '.track_changes label', function () {
          if (jquery(this).data('track') === 'on') {
            Aloha.trigger('aloha-start-tracking');
          } else {
            Aloha.trigger('aloha-stop-tracking');
          }

          checkBtnState();
        });

        // binding events
        jquery(document).on('click', '.show_changes label', function () {
          if (jquery(this).data('show') === 'yes') {
            Aloha.trigger('aloha-tracking-changes-show');
          } else {
            Aloha.trigger('aloha-tracking-changes-hide');
          }
        });

        // bind all action buttons
        jquery(document).on('click', '.tracking-action-buttons [data-trigger-aloha]', function () {
          var ev = jquery(this).data('trigger-aloha');
          Aloha.trigger('aloha-' + ev);

          if (jquery(this).hasClass('single-change')) {
            jquery('button.single-change').prop('disabled', true);
          }
        });

        // enable/disable accept/reject one change buttons
        Aloha.bind('aloha-selection-changed', function (event, rangeObject) {
          var singleChangeButtons = jquery('button.single-change');
          var elem = jquery(rangeObject.startContainer).parent();

          if (elem.is('span') && (elem.hasClass('ins') || elem.hasClass('del'))) {
            singleChangeButtons.prop('disabled', false);
          } else {
            singleChangeButtons.prop('disabled', true);
          }
        });

        // do stuff on activate tab
        iceTab.onActivate = function () {
          var value = 'off';
          if (typeof(win.booktype.tracker) !== 'undefined')
            value = win.booktype.tracker.isTracking ? 'on' : 'off';

          var option = jquery('.track_changes .track-' + value);
          var label = jquery('.track_changes label.active');

          label.removeClass('active');
          label.find('input').prop('checked', false);

          option.addClass('active');
          option.find('input').prop('checked', true);

          checkBtnState();
        };

        tabs.push(iceTab);
      }

      win.booktype.editor.activateTabs(tabs);

      // Trigger events
      jquery(document).trigger('booktype-ui-panel-active', ['edit', this]);
    };

    var _hide = function (callback) {
      delete win.booktype.tracker;
      delete win.booktype.lastSavedRange;

      _checkIfModified(function () {
        if (isZenMode) {
          jquery('body').removeClass('zenMode');
        }

        jquery('DIV.contentHeader [rel=tooltip]').tooltip('destroy');

        Aloha.jQuery('#contenteditor').mahalo();
        jquery('#content').empty();
        jquery('DIV.contentHeader').empty();

        win.booktype.editor.deactivateTabs(tabs);
        win.booktype.editor.hideAllTabs();
        jquery('#button-toc').removeClass('active');

        /* Send message to remove the lock on this chapter */
        win.booktype.sendToCurrentBook({
          'command': 'chapter_state',
          'chapterID': win.booktype.editor.getCurrentChapterID(),
          'state': 'normal'
        });

        win.booktype.editor.setCurrentChapterID(null);

        if (!_.isUndefined(callback)) {
          callback();
        }
      },
        function () {
          setTimeout(function () { jquery('#button-toc').removeClass('active'); }, 0);
        }
      );
    };

    var _init = function () {
      Aloha.bind('beforepaste', function (e) {  });

      Aloha.bind('paste', function (e) {  });

      // check if content has changed
      Aloha.bind('aloha-smart-content-changed', function (evt, args) { });
      Aloha.bind('aloha-link-selected', function () { });
      Aloha.bind('aloha-link-unselected', function () { });
      Aloha.bind('aloha-image-selected', function (a) { });
      Aloha.bind('aloha-image-unselected', function (a) { });
      Aloha.bind('aloha-editable-activated', function (evt, data) { });


      jquery('#contentModifiedModal .btn-save').on('click', function (e) {
        var _callback = _masterCallback.pop();

        jquery('#contentModifiedModal').modal('hide');
        win.booktype.editor.edit.saveContent({callback: _callback});
      });

      jquery('#contentModifiedModal .btn-cancel').on('click', function (e) {
        jquery('#contentModifiedModal').modal('hide');

        var _callback = _masterCallback.pop();
        _callback();
      });

      Aloha.bind('aloha-editable-created', function (e, editable) {
        if (editable.obj.attr('id') === 'contenteditor') {
          win.scrollTo(0, 0);

          var $p = jquery('#contenteditor').find('p');
          var $elem = null;

          if ($p.length > 0) {
            $elem = $p.get(0);
          } else {
            var $e = jquery('#contenteditor').find('*');

            if ($e.length > 0) {
              $elem = $e.get(0);
            } else {
              return;
            }
          }

          // Select first paragraph
          var newRange = new GENTICS.Utils.RangeObject();

          newRange.startContainer = newRange.endContainer = $elem;

          newRange.startOffset = newRange.endOffset = 0;
          newRange.select();

          Aloha.Selection.updateSelection();

          // This is needed for Firefox
          editable.obj.focus();

          // enable tracking if needed
          if (window.booktype.trackChanges) {
            Aloha.trigger('aloha-start-tracking');
          }

          // enable tooltips on tracking elements
          jquery('body').tooltip({
            selector: '#contenteditor:not(.CT-hide) span.ins, #contenteditor:not(.CT-hide) span.del',
            container: 'body',
            title: function () {
              var action = jquery(this).hasClass('ins') ? 'insert' : 'delete';
              var localizedAction = win.booktype._('ice_' + action + '_action', 'Modified by');

              var timeAt = win.booktype.utils.formatDate(jquery(this).data('time'), 'MM/DD/YYYY HH:mm');
              return localizedAction + ' ' + jquery(this).data('username') + ' - ' + timeAt;
            }
          });
        }
      });

      Aloha.bind('aloha-selection-changed', function (event, rangeObject) {
        win.booktype.lastSavedRange = rangeObject;
      });

      // Save notes
      jquery('.notes-tab-content #save-note').click(function () {
        var newNotes = jquery('.notes-tab-content textarea[name=notes]').val();

        win.booktype.sendToCurrentBook({
          'command': 'notes_save',
          'notes': newNotes
        },
          function (data) {
            jquery('.notes-tab-content .info').css('visibility','visible');
            setTimeout(function () { jquery('.notes-tab-content .info').css('visibility','hidden') }, 2000);
          }
        );
      });

      //Event for save with comment modal form
      jquery('#saveContentWithCommentModal button').click(function () {
        if (this.dataset.action === 'save') {
          var comment = jquery('#saveContentWithCommentModal textarea[name=comment]').val();
          win.booktype.editor.edit.saveContent({comment: comment});
        }
        jquery('#saveContentWithCommentModal textarea[name=comment]').val('');
        jquery('#saveContentWithCommentModal').modal('hide');
      });
    };

    var setChapterID = function (id) {
      chapterID = id;
    };

    return {
      'init': _init,
      'name': 'edit',
      'show': _show,
      'checkIfModified': _checkIfModified,
      'setChapterID': setChapterID,
      'getChapterID': function () { return chapterID; },
      'saveContent': saveContent,
      'disableSave': disableSave,
      'isZenMode': function() { return isZenMode; },
      'hide': _hide
    };
  })();

})(window, jQuery, _);
