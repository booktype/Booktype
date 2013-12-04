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

// the plugin currently just stores the whole chapter after every ENTER (0x0d) or simple table insert (Aloha event).
// we need to consider length of chapter and cursor position after undo
// there should also be an event when the chapter is left (saved or not) and the stack should be emptied before that happens.

define(function (require) {
        'use strict';

        var plugin;

        var block_created = false;

        var myStack = function(){
        };
        myStack.position = 0;
        myStack.stack = [];

        /**
         * Module dependencies.
         */
        var Aloha = require('aloha'),
                Plugin = require('aloha/plugin'),
                Ui = require('ui/ui'),
                Button = require('ui/button'),
                rangy = require('aloha/rangy-core'),
                $ = require('jquery');

        require('undo/vendor/undo');

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

        /**
         * Undo/redo command.
         * @type Object
         */
        var EditCommand = Undo.Command.extend({
                constructor: function (editable, contentBefore, contentAfter) {
                        this.editable = editable;
                        this.contentBefore = contentBefore;
                        this.contentAfter = contentAfter;
                },

                execute: function () {},

                undo: function () {
                        plugin.setContent(this.editable, this.contentBefore);
                },

                redo: function () {
                        plugin.setContent(this.editable, this.contentAfter);
                },
        });

        /**
         * Register the plugin with unique name.
         */
        plugin = Plugin.create('bookundo', {

                /**
                 * Initialize the plugin and set initialize flag on true.
                 */

                init: function () {
                        console.log("bookundo init");
                        console.log(myStack.position);
                        console.log(myStack.stack);
                        Aloha.bind('aloha-editable-created', plugin.onEditableCreated);
                        Aloha.bind('aloha-editable-activated', plugin.onEditableActivated);
                        Aloha.bind('aloha-table-created', plugin.blockCreated);
                        Aloha.bind('aloha-table-removed', plugin.blockRemoved);
                        console.log(plugin.stack);
                        plugin.createButtons();
                },

                blockCreated: function(){
                    block_created = true;
                    plugin.preSnapshot();
                },

                blockRemoved: function(){
                    console.log("block removed");
                    block_create = false;
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
               onEditableActivated: function (e,editable) {
                   //     plugin.updateButtons();
                   if(block_created===true){
                        plugin.blockCreated();
                   }
                   Aloha.trigger('aloha-my-undo', {'editable': editable.editable});
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
                        var content = Aloha.getEditableById('contenteditor').getContents();
                        myStack.stack.push(content);
                        myStack.position++;
                        console.log(myStack.position);
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

                        console.log(myStack.position);
                        block_created = false;
                        if(myStack.position!==0){
                            Aloha.getEditableById('contenteditor').setContents(myStack.stack.pop());
                            myStack.position--;
                        }

                },

                /**
                 * Redo the last action if possible.
                 */
                redo: function () {
                        if (plugin.stack.canRedo()) {
                                plugin.stack.redo();
                        }
                },

                /**
                 * Create the undo/redo buttons.
                 */
                createButtons: function () {
                        plugin.undoButton = Ui.adopt('bookundo', Button, {
                                tooltip: 'Undo',
                                icon: 'aloha-button-undo',
                                scope: 'Aloha.continuoustext',
                                click: function () {
                                        plugin.undo();
                                }
                        });

                        plugin.redoButton = Ui.adopt('bookredo', Button, {
                                tooltip: 'Redo',
                                icon: 'aloha-button-redo',
                                scope: 'Aloha.continuoustext',
                                click: function () {
                                        plugin.redo();
                                }
                        });

                        plugin.updateButtons();
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