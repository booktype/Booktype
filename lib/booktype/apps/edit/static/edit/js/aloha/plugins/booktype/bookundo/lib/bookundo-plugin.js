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


/*

 TODO
   - it freezes interface sometimes
   - stack should work with myStack.position and not only with the last element and list length.
   - redo does not work. to make it work myStack.position must be used
   - temporarily disabled snapshot after user pressed Enter

*/


define(
  ['aloha','aloha/plugin','ui/ui','ui/button','aloha/rangy-core','aloha/copypaste','toolbar/toolbar-plugin','jquery', 'booktype'],
  function (Aloha, Plugin, Ui, Button, rangy, CopyPaste, toolbar, $, booktype) {
        var plugin;

        var block_created = false;
        var ignoreMe = false;
        var undoFlag = false;

        // stack positions are from 0
        var current_stack_position = 0;
        var stack_length = 0;
        var myStack = {position: 0, stack: []};
 
        var initData = function () {
          block_created = false;
          ignoreMe = false;
          undoFlag = false;

          // stack positions are from 0
          current_stack_position = 0;
          stack_length = 0;
          myStack = {position: 0, stack: []};
          toolbar.disableToolbar('bookundo');
          toolbar.disableMenu('bookundo');
          toolbar.disableMenu('bookredo');
        }

        /**
         * Restore blocks in the active editor.
         */
        var enableBlocks = function () {
          if (!Aloha.settings.plugins.block.defaults) {
            Aloha.settings.plugins.block.defaults = {};
          }

          var editable = Aloha.getActiveEditable();

          if (editable !== null) {
            var $editor = $(editable.obj);

            $.each(Aloha.settings.plugins.block.defaults, function (selector, instanceDefaults) {
              $editor.find(selector).alohaBlock(instanceDefaults);
            });
          }
        }

        // breaks in blocks!!! should be corrected !!!
        var getChildElement = function(siblings, character) {
            /*
                We provide a list of siblings. For instance siblings = [2, 1, 3, 4];
                We go in reverse orders and find 4th child in $container. Then 3th child, 1st child and at the end 2nd child of the element.
            */

            var $container = $("#contenteditor");

            var inblock = false;
            if (character === 0){
              for(var n = siblings.length-1; n >= 0; n--) {
                  if($($container.children()[siblings[n]]).length > 0) {
            $container = $($container.children()[siblings[n]]);
                  }
              } 
            } else {
              for(var n = siblings.length-1; n > 0; n--) {
                  if($($container.children()[siblings[n]]).length > 0) {
            $container = $($container.children()[siblings[n]]);
                  }
                }
            }
            return $container;
        };

        var getSiblings = function($elem, lst) {
            /*
                Returns list of siblings. It checks which child it is in its parent. Then check which child is its parent and etc....
                For each parent we remember what is the position of its child.
            */
            var n = 0;

            if($elem.length === 0 || $elem.attr('id') == 'contenteditor') {
                return lst;
            }

            var $e = $elem;

            while($e.prev().length !== 0) {
                $e = $e.prev();
                n++;
            }

            lst.push(n);

            var $parent = $elem.parent();

            if(typeof parent == 'undefined') {
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
            Aloha.bind('aloha-editable-activated', plugin.onEditableActivated);

            Aloha.bind('aloha-smart-content-changed', plugin.onSmartContentChanged);

            $(document).on('booktype-document-saved', function(doc) {
              initData();
            });

            plugin.createButtons();
          },

          onSmartContentChanged: function (e, args) {
            if(!ignoreMe) {
              plugin.preSnapshot();
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
            editable.obj.bind('keyup', plugin.onKeyUp);
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
            if(editable.obj && editable.obj.attr('id') == 'contenteditor') {
              initData();
              // Do the first initial snapshot when the editor is initialized
              plugin.preSnapshot();
              disableSave(true);
            }
          },

          /**
           * Called on key down.
           */
          onKeyDown: function (e) {
            plugin.keyReleased = false;

            if(e.keyCode == 13){ // if user presses Enter take a snapshot
                // Temporarily disable snapshot after user presses Enter
                //plugin.preSnapshot();
            }


            // ignore ctrl, cmd/meta, control keys, and arrow keys
            if (e.ctrlKey || e.metaKey || e.keyCode < 32 || (e.keyCode >= 37 && e.keyCode <= 40)) {
              if (e.keyCode === 8 || e.keyCode === 46) {
                disableSave(false);
              }

              return;
            }

            // to start stack with current position if we start typing after redo/undo
            if(undoFlag===true){
              stack_length = current_stack_position;
              undoFlag = false;
            }

            // is user trying to overwrite the selection, handle it as a deletion and make a snapshot
            if (!rangy.getSelection().isCollapsed) {
              plugin.preSnapshot();
              plugin.selectionOverwrite = true;
            }

            disableSave(false);
          },
          /**
           * Called when an editable has been activated.
           */
          onEditableActivated: function (e, editable) {
            if(block_created===true){
              plugin.blockCreated();
            }
          },

          /**
           * Called before a command will be executed.
           * @param {jQuery.Event} e
           * @param {Object} obj
           */
          onCommandWillExecute: function (e, obj) {
            if (plugin.isUndoableCommand(obj.commandId)) {
              plugin.preSnapshot();
            }
          },

          /**
           * Called after a command has been executed.
           * @param {jQuery.Event} e
           * @param {String} commandId
           */
          onCommandExecuted: function (event, commandId) {
            if (plugin.isUndoableCommand(commandId)) {
              plugin.postSnapshot();
            }
          },

          /**
           * Make a snapshot and preserve selection before the content changes.
           */
          preSnapshot: function () {
            /*
               Get Range object. Try to find all the siblings from the current position. Save the list of siblings.                           
            */
            var range = Aloha.Selection.getRangeObject();
            var branches = 0;
            var range_object;

            if (range.startContainer !== undefined){
              range_object = range.getSelectionTree();
              var selected_branch_pos = 0;

              $.each(range_object, function (cnt,el) {
                if (el.selection !== "none") {
                  selected_branch_pos = cnt;
                }
              });
              branches = selected_branch_pos;
            }
            var editable = Aloha.getEditableById('contenteditor');

            if (!editable) {
              return;
            }

            var content = {data: editable.getContents(),
              character: range.startOffset,
              branches: branches,
              siblings: getSiblings($(range.startContainer), []),
              position: {y: $(window).scrollTop(),
                x: $(window).scrollLeft()}
              };

            if(stack_length > 0) {
              /* Compare current chapter content to the one in stash with current stack position. Do not do snapshot if they are the same */
              if(myStack.stack[current_stack_position-1].data === content.data) {
                  return;
              }
            }


            myStack.stack[current_stack_position] = content;
            stack_length++;
            current_stack_position++;
            // when we have something on the stack enable undo button
            if (stack_length===2){
              toolbar.enableToolbar('bookundo');
              toolbar.enableMenu('bookundo');
              toolbar.disableMenu('bookredo');                          
            }
            if(current_stack_position<stack_length){
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

            editable.obj.html(content);

            Aloha.trigger('aloha-undo-content-changed', data);
          },

          /**
           * Check if the given command should produce an entry in the undo stack.
           * @param  {String} commandId
           * @return {Boolean}
           */
          isUndoableCommand: function (commandId) {
            return (commandId === 'delete' || commandId === 'insertHTML');
          },

          /**
           * Undo the last action if possible.
           */
          undo: function () {
            undoFlag = true;
            block_created = false;

            if(stack_length > 0) {
              if(current_stack_position>0){
                current_stack_position--;
              }

              var new_content = myStack.stack[current_stack_position-1];
              if(typeof new_content === 'undefined') {
                   return;
               }

               // Set flag so we don't trigger event in the event callback
              ignoreMe = true;

              Aloha.getEditableById('contenteditor').setContents(new_content.data);

              Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});

              var sel = window.getSelection();
              var scrollPositionBeforePaste = new_content.position;

              window.scrollTo(
                  scrollPositionBeforePaste.x,
                  scrollPositionBeforePaste.y
              );

              /*
                 If list of siblings has element we try to grab the element.
              */
              if(new_content.siblings.length > 0) {
                /*
                  Find the element.
                */

                var $node = getChildElement(new_content.siblings, new_content.character);
                // add part of the tree to $node so character position works as advertised!!!

                // If element exists
                if($node.length > 0) {
                  // Try to select the node. We don't care about exact position now. More or less happy
                  // to select anything.
                  var newRange = new GENTICS.Utils.RangeObject();
                  newRange.startContainer = newRange.endContainer = $node[0];

                  if(new_content.character!==0){ // selection is partial
                    newRange.startOffset = new_content.branches;
                    newRange.endOffset = new_content.branches+1;
                    newRange.select();
                  } else { // selection is colapsed
                    newRange.startOffset = 0;
                    newRange.endOffset = 0;
                    newRange.select();
                  }

                  Aloha.Selection.updateSelection();
                  range = Aloha.Selection.rangeObject;
                  range.startOffset = new_content.character;
                  range.endOffset = new_content.character;
                  range.select();

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
            block_created = false;

            if(current_stack_position < stack_length) {
              var range = Aloha.Selection.getRangeObject();

              current_stack_position++;
              var new_content = myStack.stack[current_stack_position-1];

              ignoreMe = true;

              Aloha.getEditableById('contenteditor').setContents(new_content.data);

              Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});

              var sel = window.getSelection();
              var scrollPositionBeforePaste = new_content.position;

              window.scrollTo(
                  scrollPositionBeforePaste.x,
                  scrollPositionBeforePaste.y
              );
              /*
                 If list of siblings has element we try to grab the element.
              */
              if(new_content.siblings.length > 0) {
                /*
                  Find the element.
                */
                var $node = getChildElement(new_content.siblings, new_content.character);

                // If element exists
                if($node.length > 0) {
                  // Try to select the node. We don't care about exact position now. More or less happy
                  // to select anything.
                  var newRange = new GENTICS.Utils.RangeObject();
                  newRange.startContainer = newRange.endContainer = $node[0];

                  if(new_content.character!==0){ // selection is partial
                    newRange.startOffset = new_content.branches;
                    newRange.endOffset = new_content.branches+1;
                    newRange.select();
                  } else { // selection is colapsed
                    newRange.startOffset = 0;
                    newRange.endOffset = 0;
                    newRange.select();
                  }

                  Aloha.Selection.updateSelection();
                  range = Aloha.Selection.rangeObject;
                  range.startOffset = new_content.character;
                  range.endOffset = new_content.character;
                  range.select();
                  
                }
              }
            }
            if(current_stack_position===stack_length){
              toolbar.enableToolbar('bookundo');
              toolbar.enableMenu('bookundo');
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