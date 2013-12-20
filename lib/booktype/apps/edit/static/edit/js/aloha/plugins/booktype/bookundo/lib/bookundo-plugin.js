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


define(['require','undo/vendor/diff_match_patch_uncompressed'],function (require) {
        var plugin;

        var block_created = false;
        var ignoreMe = false;

        var myStack = {position: 0, stack: []};
 
        /**
         * Module dependencies.
         */
        var Aloha = require('aloha'),
            Plugin = require('aloha/plugin'),
            Ui = require('ui/ui'),
            Button = require('ui/button'),
            rangy = require('aloha/rangy-core'),
            CopyPaste = require('aloha/copypaste'),
            $ = require('jquery');

        var
          dmp = new diff_match_patch,
          resetFlag = false;


 
        /**
         * Restore blocks in the active editor.
         */
        function enableBlocks() {
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

        var getChildElement = function(siblings) {
            /*
                We provide a list of siblings. For instance siblings = [2, 1, 3, 4];
                We go in reverse orders and find 4th child in $container. Then 3th child, 1st child and at the end 2nd child of the element.
            */

            var $container = $("#contenteditor");

            for(var n = siblings.length-1; n >= 0; n--) {
                if($($container.children()[siblings[n]]).length > 0)
                    $container = $($container.children()[siblings[n]]);

                console.log($container);
            }

            return $container;
        }

        var getSiblings = function($elem, lst) {            
            /*
                Returns list of siblings. It checks which child it is in its parent. Then check which child is its parent and etc....
                For each parent we remember what is the position of its child.
            */
            
            var n = 0;

            if($elem.length == 0 || $elem.attr('id') == 'contenteditor') {
                return lst;
            }

            var $e = $elem; 

            while($e.prev().length != 0 || n > 10) {
                $e = $e.prev();
                n++;                
            }

            lst.push(n);

            var $parent = $elem.parent();

            if(typeof parent == 'undefined') {
                return lst;
            }

            return getSiblings($parent, lst);
        }

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

                        // Temporarily disabled
                        //Aloha.bind('aloha-table-created', plugin.blockCreated);
                        //Aloha.bind('aloha-table-removed', plugin.blockRemoved);

                        plugin.createButtons();
                },

                blockCreated: function(){
                    block_created = true;
                    plugin.preSnapshot();
                },

                blockRemoved: function(){
                    block_create = false;
                },

                onSmartContentChanged: function(e, args) {
                    console.log('[BOOK UNDO] aloha-smart-content-changed ', ignoreMe);

                    if(!ignoreMe) {
                        plugin.preSnapshot();
                    } else {
                        ignoreMe = false;
                    }
                },

                /**
                 * Called after a new editable has been created.
                 * @param {jQuery.Event} e
                 * @param {Aloha.Editable} editable
                 */
                onEditableCreated: function (e, editable) {
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
                            myStack = {position: 0, stack: []};
                            
                            // Do the first initial snapshot when the editor is initialized
                            plugin.preSnapshot();
                        }
                },

                /**
                 * Called on key down.
                 */
                onKeyDown: function (e) {
                        plugin.keyReleased = false;

                        if(e.keyCode == 13){ // if user presses Enter take a snapshot
                            plugin.preSnapshot();
                        }


                        // ignore ctrl, cmd/meta, control keys, and arrow keys
                        if (e.ctrlKey || e.metaKey || e.keyCode < 32 || (e.keyCode >= 37 && e.keyCode <= 40)) {
                                return;
                        }

                        // is user trying to overwrite the selection, handle it as a deletion and make a snapshot
                        if (!rangy.getSelection().isCollapsed) {
                                plugin.preSnapshot();
                                plugin.selectionOverwrite = true;
                        }
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
                        var content = {data: Aloha.getEditableById('contenteditor').getContents(),
                                       siblings: getSiblings($(range.startContainer), []),
                                       position: {y: $(window).scrollTop(),
                                                  x: $(window).scrollLeft()}
                                      };

                        if(myStack.stack.length > 1) {
                            /* Compare current chapter content to the last one in stash. Do not do snapshot if they are the same */
                            if(myStack.stack[myStack.stack.length-1].data === content.data) {
                                return;
                            }                            
                        }

                        console.log('[BOOK UNDO] makingSnapshot = ', myStack.stack.length);

                        myStack.stack.push(content);
                        myStack.position++;
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
                        block_created = false;

                        if(myStack.stack.length > 0) {
                            console.log('[BOOK UNDO] undoing position = ', myStack.stack.length);

                            var new_content = myStack.stack.pop();

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
                                var $node = getChildElement(new_content.siblings);

                                // If element exists
                                if($node.length > 0) {
                                    console.log($node[0]);

                                    // Try to select the node. We don't care about exact position now. More or less happy
                                    // to select anything.
                                    var newRange = new GENTICS.Utils.RangeObject();

                                    newRange.startContainer = newRange.endContainer = $node[0];
                                    newRange.startOffset = 0;
                                    newRange.endOffset = newRange.startOffset + 1;
                                    newRange.select();
                                }
                            }

                            myStack.position--;
                        }
                },

                /**
                 * Redo the last action if possible.
                 */

                redo: function () {
                        block_created = false;

                        if(myStack.stack.length > 1) {
                            var top_of_the_stack_pos = myStack.stack.length-1;

                            var patch = dmp.patch_make(myStack.stack[myStack.stack.length-1].data, myStack.stack[myStack.stack.length-2].data);
                            // let's change the patch data from delete to include (from -1 to 1) but only if there is a difference
                            if(patch.length!==0){
                              jQuery.each(patch[0].diffs,function(cnt,e){
                                if(e[0]===-1){
                                  e[0]=1;
                                  console.log(e[1]);
                                }
                              });
                              var applied = dmp.patch_apply(patch, myStack.stack[myStack.stack.length-1].data);
                              var range = Aloha.Selection.getRangeObject();

                              var content = {data: applied[0],
                                             siblings: getSiblings($(range.startContainer), []),
                                             position: {y: $(window).scrollTop(),
                                                        x: $(window).scrollLeft()}
                                          };
                              myStack.stack.push(content);

                              ignoreMe = true;

                              Aloha.getEditableById('contenteditor').setContents(content.data);
                              Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});

                              var sel = window.getSelection();
                              var scrollPositionBeforePaste = content.position;

                              window.scrollTo(
                                  scrollPositionBeforePaste.x,
                                  scrollPositionBeforePaste.y
                              );
                            }

                        }
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