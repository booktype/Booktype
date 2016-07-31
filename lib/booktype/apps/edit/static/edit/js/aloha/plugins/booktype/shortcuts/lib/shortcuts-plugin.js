define([
    'aloha',
    'aloha/plugin',
    'aloha/copypaste',
    'jquery19'
  ],
  function (Aloha, Plugin, CopyPaste, jQuery) {
    'use strict';

    var actions = {
      selectAll: function (event, editor) {
        var el = editor;
        var start = getFirstSelectableChild(el);
        var end = getLastSelectableChild(el);

        CopyPaste.setSelectionAt({
          startContainer: start,
          endContainer: end,
          startOffset: 0,
          endOffset: end.length
        });

        return false;
      }
    };

    var shortcuts = Plugin.create('shortcuts', {
      defaultSettings: {
        enabled: true,

        keycodes: {
          65: 'a'
        },

        /**
         * Map to handle multiple key combinations. Each handler function
         * should receive as parameter an {jQuery.Event} event and
         * the {HTMLElement} editor element. Also the handler should return
         * to stop the propagation of the event
         */
        bindingsMap: {
          'ctrl+a': actions.selectAll
        },

        mainEditor: 'contenteditor'
      },

      init: function () {
        var plugin = this;

        plugin.settings = jQuery.extend(
          true, plugin.defaultSettings, plugin.settings
        );

        if (!plugin.settings.enabled)
          return;

        // like always, listening to desired events
        plugin.bindEvents();
      },

      bindEvents: function () {
        var plugin = this;

        jQuery(document).on('keydown', function (event) {
          return plugin.onKeydown(event);
        });
      },

      // Improved piece of code taken from aloha/editable.js
      onKeydown: function (event) {
        var plugin = this;

        if (!Aloha.activeEditable) {
          return;
        }

        var editor = document.getElementById(plugin.settings.mainEditor);
        var key = plugin.settings.keycodes[event.which];

        if (key) {
          // try to get a keys combination and execute the registered action
          var modifier = plugin.keyModifier(event);
          var combo = (modifier ? modifier + '+' : '') + key;

          // if a handler functions is found, triggers it
          var handler = plugin.settings.bindingsMap[combo];
          if (handler) {
            return handler(event, editor);
          }
        }
      },

      // another piece of code taken from aloha/editable.js
      keyModifier: function (event) {
        return event.altKey ? 'alt' :
              (event.ctrlKey || event.metaKey) ? 'ctrl' :
                event.shiftKey ? 'shift' : null;
      }
    });

    /* Utility functions taken from icejs but improved to work here */
    function getFirstSelectableChild(element) {
      var TEXT_NODE = 3;

      if (element) {
        if (element.nodeType !== TEXT_NODE) {
          var child = element.firstChild;
          while (child) {
            if (isSelectable(child) === true) {
              return child;
            } else if (child.firstChild) {
              // This node does have child nodes.
              var res = getFirstSelectableChild(child);
              if (res !== null) {
                return res;
              } else {
                child = child.nextSibling;
              }
            } else {
              child = child.nextSibling;
            }
          }
        } else {
          // Given element is a text node so return it.
          return element;
        }
      }
      return null;
    }

    function getLastSelectableChild(element) {
      var TEXT_NODE = 3;

      if (element) {
        if (element.nodeType !== TEXT_NODE) {
          var child = element.lastChild;
          while (child) {
            if (isSelectable(child) === true) {
              return child;
            } else if (child.lastChild) {
              // This node does have child nodes.
              var res = getLastSelectableChild(child);
              if (res !== null) {
                return res;
              } else {
                child = child.previousSibling;
              }
            } else {
              child = child.previousSibling;
            }
          }
        } else {
          // Given element is a text node so return it.
          return element;
        }
      }
      return null;
    }

    function isSelectable(container) {
      var TEXT_NODE = 3;

      if (container && container.nodeType === TEXT_NODE && container.data.length !== 0) {
        return true;
      }
      return false;
    }
    /* end of utility functions */

    return shortcuts;
  }
);