/* undo-plugin.js is part of Aloha Editor project http://aloha-editor.org
 *
 * Aloha Editor is a WYSIWYG HTML5 inline editing library and editor.
 * Copyright (c) 2010-2012 Gentics Software GmbH, Vienna, Austria.
 * Contributors http://aloha-editor.org/contribution.php
 *
 * Aloha Editor is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or any later version.
 *
 * Aloha Editor is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * As an additional permission to the GNU GPL version 2, you may distribute
 * non-source (e.g., minimized or compacted) forms of the Aloha-Editor
 * source code without the copy of the GNU GPL normally required,
 * provided you include this license notice and a URL through which
 * recipients can access the Corresponding Source.
 */

define(
  ['aloha', 'aloha/plugin', 'ui/ui', 'ui/button', 'aloha/rangy-core', 'aloha/copypaste', 'toolbar/toolbar-plugin', 'jquery', 'booktype', 'PubSub', 'bookundo/diff_match_patch'],
  function (Aloha, Plugin, Ui, Button, rangy, CopyPaste, toolbar, $, booktype, PubSub, diff_match_patch) {
    var plugin;

    // diff match patch object
    var dmp;

    var timeout_id;
    var nonStopChars = 0;
    var subscriptionID = null;

    var ignoreMe = false;
    var undoFlag = false;

    // stack positions are from 0
    var current_stack_position = 0;
    var stack_length = 0;
    var myStack = [];

    var initData = function () {
      ignoreMe = false;
      undoFlag = false;

      // create a new diff_match_patch object
      dmp = new window.diff_match_patch();

      // stack positions are from 0
      current_stack_position = 0;
      stack_length = 0;
      myStack = [];

      toolbar.disableToolbar('bookundo');
      toolbar.disableMenu('bookundo');
      toolbar.disableMenu('bookredo');
    };

    // breaks in blocks!!! should be corrected !!!
    var getChildElement = function (siblings, character) {
      /*
       We provide a list of siblings. For instance siblings = [2, 1, 3, 4];
       We go in reverse orders and find 4th child in $container. Then 3th child, 1st child and at the end 2nd child of the element.
       */

      var $container = $("#contenteditor");

      if (character === 0) {
        for (var n = siblings.length - 1; n >= 0; n--) {
          if ($($container.children()[siblings[n]]).length > 0) {
            $container = $($container.children()[siblings[n]]);
          }
        }
      } else {
        for (var n = siblings.length - 1; n > 0; n--) {
          if ($($container.children()[siblings[n]]).length > 0) {
            $container = $($container.children()[siblings[n]]);
          }
        }
      }
      return $container;
    };

    var getSiblings = function ($elem, lst) {
      /*
       Returns list of siblings. It checks which child it is in its parent. Then check which child is its parent and etc....
       For each parent we remember what is the position of its child.
       */
      var n = 0;

      if ($elem.length === 0 || $elem.attr('id') == 'contenteditor') {
        return lst;
      }

      var $e = $elem;

      while ($e.prev().length !== 0) {
        $e = $e.prev();
        n++;
      }

      lst.push(n);

      var $parent = $elem.parent();

      if (typeof parent == 'undefined') {
        return lst;
      }

      return getSiblings($parent, lst);
    };

    var disableSave = function (state) {
      booktype.editor.edit.disableSave(state);
    };

    /**
     * Register the plugin with unique name.
     */
    plugin = Plugin.create('bookundo', {

      /**
       * Initialize the plugin and set initialize flag on true.
       */

      init: function () {
        Aloha.bind('aloha-editable-created', plugin.onEditableCreated);
        Aloha.bind('aloha-smart-content-changed', plugin.onSmartContentChanged);

        $(document).on('booktype-document-saved', function (doc) {
          initData();
        });

        plugin.createButtons();
      },

      onSmartContentChanged: function (e, args) {
        if (!ignoreMe) {
          plugin.snapshot();
          PubSub.pub('bookundo.snapshot.created', {'reason': 'smart-content-changed'});
        } else {
          ignoreMe = false;
        }

        var editable = Aloha.getEditableById('contenteditor');

        if (editable && editable.isModified()) {
          disableSave(false);
        }
      },

      /**
       * Called after a new editable has been created.
       * @param {jQuery.Event} e
       * @param {Aloha.Editable} editable
       */
      onEditableCreated: function (e, editable) {
        ignoreMe = false;
        editable.obj.bind('keydown', plugin.onKeyDown);
        editable.obj.bind('keydown', 'ctrl+z meta+z ctrl+shift+z meta+shift+z', function (event) {
          event.preventDefault();
          if (event.shiftKey) {
            plugin.redo();
          } else {
            plugin.undo();
          }
        });

        /*
         Every time main editor is initialized (for instance user has selected new chapter) we delete our stack.
         */
        if (editable.obj && editable.obj.attr('id') == 'contenteditor') {
          initData();
          // Do the first initial snapshot when the editor is initialized
          plugin.snapshot();
          PubSub.pub('bookundo.snapshot.created', {'reason': 'initial'});

          disableSave(true);
        }

        // init toolbar observer and subscribe to the channel
        if (subscriptionID) {
          PubSub.unsub(subscriptionID);
        }

        // subscribe to toolbar.action.triggered messages
        subscriptionID = PubSub.sub('toolbar.action.triggered', function (message) {

          var $target = $(message.event.currentTarget);
          if ($target.hasClass('bookundo') || $target.hasClass('bookredo')) { return; }

          setTimeout(function () {
            var editable = Aloha.getEditableById('contenteditor');
            if (stack_length > 0) {
              if (!_.isUndefined(myStack[current_stack_position - 1]) &&
                  myStack[current_stack_position - 1].getData() !== editable.getContents()) {

                // to start stack with current position if content was changed through toolbar after redo/undo
                if (undoFlag === true) {
                  stack_length = current_stack_position;
                  undoFlag = false;
                }

                plugin.snapshotVirtual();

                // this is required for firefox
                if (Aloha.browser.mozilla)
                  $('#contenteditor').focus();

                // publish notification that snapshot was created
                PubSub.pub('bookundo.snapshot.created', {
                  'reason': 'toolbar-action',
                  'snapshot': myStack[current_stack_position - 1]
                });
              }
            }
          }, 200);
        });

      },

      /**
       * Called on key down.
       */
      onKeyDown: function (e) {
        plugin.keyReleased = false;

        // ignore ctrl, cmd/meta, control keys, and arrow keys
        if (e.ctrlKey || e.metaKey || e.keyCode < 32 || (e.keyCode >= 37 && e.keyCode <= 40)) {
          if (e.keyCode === 8 || e.keyCode === 46) {
            disableSave(false);
          }
          return;
        }

        // we call doCleanup on almost every keydown
        // to prevent async range changing in case fast typing
        var rangeObject = Aloha.Selection.getRangeObject();
        if (GENTICS.Utils.Dom.doCleanup({'merge': true}, rangeObject, rangeObject.getCommonAncestorContainer())) {
          rangeObject.update();
          rangeObject.select();
        }

        // to start stack with current position if we start typing after redo/undo
        if (undoFlag === true) {
          stack_length = current_stack_position;
          undoFlag = false;
        }

        // is user trying to overwrite the selection, handle it as a deletion and make a snapshot
        if (!rangy.getSelection().isCollapsed) {
          plugin.snapshot();
          plugin.selectionOverwrite = true;

          PubSub.pub('bookundo.snapshot.created', {'reason': 'direct-change'});
        }

        // if we write faster than setTimeout's delay -> terminate async call
        clearTimeout(timeout_id);

        if (nonStopChars > 5) {
          plugin.snapshotVirtual();
          nonStopChars = 0;

          PubSub.pub('bookundo.snapshot.created', {'reason': 'direct-change'});
        } else {
          timeout_id = setTimeout(function () {
            plugin.snapshotVirtual();
            nonStopChars = 0;

            PubSub.pub('bookundo.snapshot.created', {'reason': 'direct-change'});
          }, 150);

          nonStopChars++;
        }

        disableSave(false);
      },

      /**
       * Make a snapshot and preserve selection before the content changes.
       */
      snapshot: function () {
        /*
         Get Range object. Try to find all the siblings from the current position. Save the list of siblings.
         */
        var range = Aloha.Selection.getRangeObject();
        var editable = Aloha.getEditableById('contenteditor');
        var branches = 0;
        var range_object;

        if (!editable) {
          return;
        }

        if (range.startContainer !== undefined) {
          range_object = range.getSelectionTree();
          var selected_branch_pos = 0;

          $.each(range_object, function (cnt, el) {
            if (el.selection !== "none") {
              selected_branch_pos = cnt;
            }
          });
          branches = selected_branch_pos;
        }

        var stackItem = {
          isVirtual: false,
          getData: function () {
            return this._data;
          },
          character: range.startOffset,
          branches: branches,
          siblings: getSiblings($(range.startContainer), []),
          position: {
            y: $(window).scrollTop(),
            x: $(window).scrollLeft()
          },
          _data: editable.getContents()
        };

        if (stack_length > 0) {

          // this condition can be redundant, but possibly it can prevent some strange behaivor exceptions
          if (typeof myStack[current_stack_position - 1] === 'undefined') { return; }

          /* Compare current chapter content to the one in stash with current stack position. Do not do snapshot if they are the same */
          if (myStack[current_stack_position - 1].getData() === stackItem.getData()) {
            return;
          }
        }

        myStack[current_stack_position] = stackItem;
        stack_length++;
        current_stack_position++;

        // when we have something on the stack enable undo button
        if (stack_length >= 2) {
          toolbar.enableToolbar('bookundo');
          toolbar.enableMenu('bookundo');
          toolbar.disableMenu('bookredo');
        }
        if (current_stack_position < stack_length) {
          toolbar.enableMenu('bookredo');
        }
      },

      /**
       * Make a virtual (patched) snapshot and preserve selection before the content changes.
       */
      snapshotVirtual: function () {
        /*
         Get Range object. Try to find all the siblings from the current position. Save the list of siblings.
         */
        var range = Aloha.Selection.getRangeObject();
        var editable = Aloha.getEditableById('contenteditor');
        var branches = 0;
        var range_object;
        var stackItem;

        if (!editable) {
          return;
        }

        // get latest non virtual snapshot
        for (var i = myStack.length - 1; i >= 0; i--) {
          if (!myStack[i].isVirtual) {
            stackItem = myStack[i];
          }
        }

        if (!stackItem) {
          return;
        }

        var patch_list = dmp.patch_make(stackItem.getData(), editable.getContents());
        var patch_text = dmp.patch_toText(patch_list);

        if (range.startContainer !== undefined) {
          range_object = range.getSelectionTree();
          var selected_branch_pos = 0;

          $.each(range_object, function (cnt, el) {
            if (el.selection !== "none") {
              selected_branch_pos = cnt;
            }
          });
          branches = selected_branch_pos;
        }

        var stackItemVirtual = {
          isVirtual: true,
          getData: function () {
            return dmp.patch_apply(
              dmp.patch_fromText(this._data),
              stackItem.getData())[0]
          },
          character: range.startOffset,
          branches: branches,
          siblings: getSiblings($(range.startContainer), []),
          position: {
            y: $(window).scrollTop(),
            x: $(window).scrollLeft()
          },
          _data: patch_text
        };

        myStack[current_stack_position] = stackItemVirtual;
        stack_length++;
        current_stack_position++;

        // when we have something on the stack enable undo button
        if (stack_length >= 2) {
          toolbar.enableToolbar('bookundo');
          toolbar.enableMenu('bookundo');
          toolbar.disableMenu('bookredo');
        }
        if (current_stack_position < stack_length) {
          toolbar.enableMenu('bookredo');
        }
      },

      /**
       * Update the content on the editable with the given content and restore the selection.
       * @param  {Aloha.Editable} editable
       * @param  {String} content
       * @param  {Object} bookmark
       */
      setContent: function (editable, content, bookmark) {
        var data = {
          editable: editable,
          content: content
        };

        Aloha.trigger('aloha-undo-content-will-change', data);

        // editable.obj.html(content);
        editable.setContents(content);

        Aloha.trigger('aloha-undo-content-changed', data);
      },

      /**
       * Undo the last action if possible.
       */
      undo: function () {
        undoFlag = true;

        if (stack_length > 0) {
          if (current_stack_position <= 0) { return; }

          current_stack_position--;

          var stackItem = myStack[current_stack_position - 1];
          if (typeof stackItem === 'undefined') {
            current_stack_position++;
            return;
          }

          // Set flag so we don't trigger event in the event callback
          ignoreMe = true;

          Aloha.getEditableById('contenteditor').setContents(stackItem.getData());

          Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});

          var scrollPositionBeforePaste = stackItem.position;

          // if (current_stack_position !== 1) {
          //   window.scrollTo(
          //     scrollPositionBeforePaste.x,
          //     scrollPositionBeforePaste.y
          //   );
          // }

          /*
           If list of siblings has element we try to grab the element.
           */
          if (stackItem.siblings.length > 0) {
            /*
             Find the element.
             */

            var $node = getChildElement(stackItem.siblings, stackItem.character);
            // add part of the tree to $node so character position works as advertised!!!

            // If element exists
            if ($node.length > 0) {

              // this is required for firefox
              $('#contenteditor').focus();

              // Try to select the node. We don't care about exact position now. More or less happy
              // to select anything.
              var newRange = new GENTICS.Utils.RangeObject();
              newRange.startContainer = newRange.endContainer = $node[0];

              try {
                if (stackItem.character !== 0) { // selection is partial
                  newRange.startOffset = stackItem.branches;
                  newRange.endOffset = stackItem.branches + 1;
                  try {
                    newRange.select();
                  } catch (err) {
                  }
                } else { // selection is colapsed
                  newRange.startOffset = 0;
                  newRange.endOffset = 0;
                  try {
                    newRange.select();
                  } catch (err) {
                  }
                }
              } catch (err) {
                newRange.startOffset = 0;
                newRange.endOffset = 0;
                newRange.select();
              }

              Aloha.Selection.updateSelection();
              var range = Aloha.Selection.rangeObject;
              range.startOffset = stackItem.character;
              range.endOffset = stackItem.character;
              try {
                range.select();
              } catch (err) {
              }
            }
          }
        }

        if (current_stack_position === 1) {
          toolbar.disableToolbar('bookundo');
          toolbar.disableMenu('bookundo');
        }

        if (current_stack_position < stack_length) {
          toolbar.enableMenu('bookredo');
        }
        disableSave(false);
      },

      /**
       * Redo the last action if possible.
       */

      redo: function () {
        if (current_stack_position < stack_length) {
          var range = Aloha.Selection.getRangeObject();

          current_stack_position++;
          var stackItem = myStack[current_stack_position - 1];

          if (typeof stackItem === 'undefined') {
            current_stack_position--;
            return;
          }

          ignoreMe = true;

          Aloha.getEditableById('contenteditor').setContents(stackItem.getData());

          Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});

          var scrollPositionBeforePaste = stackItem.position;

          window.scrollTo(
            scrollPositionBeforePaste.x,
            scrollPositionBeforePaste.y
          );
          /*
           If list of siblings has element we try to grab the element.
           */
          if (stackItem.siblings.length > 0) {
            /*
             Find the element.
             */
            var $node = getChildElement(stackItem.siblings, stackItem.character);

            // If element exists
            if ($node.length > 0) {

              // this is required for firefox
              $('#contenteditor').focus();

              // Try to select the node. We don't care about exact position now. More or less happy
              // to select anything.
              var newRange = new GENTICS.Utils.RangeObject();
              newRange.startContainer = newRange.endContainer = $node[0];

              try {
                if (stackItem.character !== 0) { // selection is partial
                  newRange.startOffset = stackItem.branches;
                  newRange.endOffset = stackItem.branches + 1;
                  newRange.select();
                } else { // selection is colapsed
                  newRange.startOffset = 0;
                  newRange.endOffset = 0;
                  newRange.select();
                }
              } catch (err) {
                newRange.startOffset = 0;
                newRange.endOffset = 0;
                newRange.select();
              }

              Aloha.Selection.updateSelection();
              range = Aloha.Selection.rangeObject;
              range.startOffset = stackItem.character;
              range.endOffset = stackItem.character;
              range.select();

            }
          }
        }

        if (current_stack_position !== 1) {
          toolbar.enableToolbar('bookundo');
          toolbar.enableMenu('bookundo');
        }

        if (current_stack_position === stack_length) {
          toolbar.disableMenu('bookredo');
        }

        disableSave(false);
      },

      /**
       * Create the undo/redo buttons.
       */
      createButtons: function () {
        plugin.undoButton = Ui.adopt('bookundo', null, {
          tooltip: 'Undo',
          icon: 'aloha-button-undo',
          scope: 'Aloha.continuoustext',
          click: function () {
            plugin.undo();
          }
        });

        plugin.redoButton = Ui.adopt('bookredo', null, {
          tooltip: 'Redo',
          icon: 'aloha-button-redo',
          scope: 'Aloha.continuoustext',
          click: function () {
            plugin.redo();
          }
        });
      },

      /**
       * toString method.
       * @return String
       */
      toString: function () {
        return 'bookundo';
      }
    });

    return plugin;
  });
