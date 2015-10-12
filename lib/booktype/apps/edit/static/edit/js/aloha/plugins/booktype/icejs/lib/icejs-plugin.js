define(
  ['aloha', 'aloha/plugin', 'aloha/engine', 'aloha/selection', 'PubSub', 'jquery', 'jquery19', 'booktype'],
  function (Aloha, Plugin, Engine, Selection, PubSub, jQuery, jQuery19, booktype) {
    'use strict';

    // this variable is flag for dirty hack with backspace
    var activateTrackingOnKeyUp = false;

    var icejsPlugin = Plugin.create('icejs', {

      initICE: function (callback) {
        // if tracker is already initiated, nothing to do here
        if (jQuery('#contenteditor').data('ice-initiated') === true) return {};

        var username = booktype.fullname.length > 0 ? booktype.fullname : booktype.username;

        booktype.tracker = new ice.InlineChangeEditor({
          element: jQuery('#contenteditor')[0],
          handleEvents: true,
          currentUser: {id: booktype.username, name: username},
          customDeleteHandler: function(range, direction){
            // do more research about value param for aloha methods, just faking it for now
            var value = '';

            // direction: left -> backspace delete, right -> forward delete
            var deleteFunc = (direction === 'left') ? window.alohaDelete : window.alohaForwardDelete;
            deleteFunc.action(value, range);
          },
          plugins: [
            {
              name: 'IceCopyPastePlugin',
              settings: {
                // Tags and attributes to preserve when cleaning a paste
                preserve: 'p,a[href],span[id,class]em,strong'
              }
            }
          ]
        });

        // set attribute, so we just enable once
        jQuery('#contenteditor').data('ice-initiated', true);

        if (typeof(callback) === 'function')
          callback(booktype.tracker);
      },

      stopAlohaTracking: function () {
        booktype.tracker.disableChangeTracking();

        // restore aloha overridden commands
        Engine.commands.delete = window.alohaDelete;
        Engine.commands.forwarddelete = window.alohaForwardDelete;
      },

      overrideMethods: function () {
        // fake method to avoid double deleting when tracking is On
        var alohaFakeDelete = {
          action: function (value, range) {}
        };

        // backup old delete command
        window.alohaDelete = Engine.commands.delete;
        window.alohaForwardDelete = Engine.commands.forwarddelete;

        // override default methods
        Engine.commands.delete = alohaFakeDelete;
        Engine.commands.forwarddelete = alohaFakeDelete;
      },

      registerEventHandlers: function () {
        // backspace
        Aloha.Markup.addKeyHandler(8, function (event) {
          var range = booktype.tracker.getCurrentRange();
          var contentAddNode = booktype.tracker.getIceNode(range.startContainer, 'insertType');
          if (booktype.tracker._currentUserIceNode(contentAddNode)) {
            icejsPlugin.stopAlohaTracking();
            icejsPlugin.removeEventHandlers();
            activateTrackingOnKeyUp = true;
            return true;
          }

          // only if mozilla or the active contenteditable is not editor, like title tag or tables
          if (Aloha.browser.mozilla || event.target !== jQuery('#contenteditor')[0]) {
            return booktype.tracker._handleAncillaryKey(event);
          }
        });

        Aloha.Markup.addKeyHandler(46, function (event) {
          if (Aloha.browser.mozilla || event.target !== jQuery('#contenteditor')[0]) {
            return booktype.tracker._handleAncillaryKey(event);
          }
        });
      },

      removeEventHandlers: function () {
        jQuery.each([8, 46], function (idx, keyCode) {
          Aloha.Markup.removeKeyHandler(keyCode);
        });
      },

      hideTooltips: function () {
        jQuery(document).find('.tooltip.fade.in').hide().removeClass('fade in');
      },

      init: function () {
        var plugin = this;

        // this bind is to start tracking manually even
        // if booktype.trackChanges is false
        Aloha.bind('aloha-start-tracking', function (e) {
          if (typeof(booktype.tracker) !== 'undefined') {
            booktype.tracker.enableChangeTracking();
            plugin.registerEventHandlers();
          } else {
            plugin.initICE(function (tracker) {
              tracker.startTracking();
              plugin.registerEventHandlers();
              plugin.overrideMethods();
            });
          }
        });

        Aloha.bind('aloha-editable-created', plugin.onEditableCreated);

        // if aloha editor gets destroyed, stop tracking engine
        Aloha.bind('aloha-editable-destroyed', function (e, editable) {
          Aloha.bind('aloha-stop-tracking');
        });

        // this is to manually stop tracking changes
        Aloha.bind('aloha-stop-tracking', function () {
          plugin.stopAlohaTracking();
          plugin.removeEventHandlers();
        });

        // accept all changes
        Aloha.bind('aloha-tracking-accept-all', function () {
          booktype.tracker.acceptAll();
        });

        // decline all changes
        Aloha.bind('aloha-tracking-decline-all', function () {
          booktype.tracker.rejectAll();
        });

        // accept one changes
        Aloha.bind('aloha-tracking-accept-one', function () {
          booktype.tracker.acceptChange();
        });

        // decline one changes
        Aloha.bind('aloha-tracking-decline-one', function () {
          booktype.tracker.rejectChange();
        });

        // show / hide changes in editor
        Aloha.bind('aloha-tracking-changes-show', function () {
          jQuery('#contenteditor').removeClass('CT-hide');
        });

        Aloha.bind('aloha-tracking-changes-hide', function () {
          jQuery('#contenteditor').addClass('CT-hide');
        });

        // hide all tracking tooltips when my-undo is activaded
        Aloha.bind('aloha-my-undo', function () {
          plugin.hideTooltips();
        });

        PubSub.sub('toolbar.action.after_execution', function (data) {
          plugin.trackToolbarAction(data);
        });

        jQuery(document).on('keyup', function () {
          plugin.hideTooltips();
        });

        PubSub.sub('aloha.selection.context-change', function (data) {
          plugin.checkFormattingButtons(data.range);
        });
      },

      /**
       * Called after a new editable has been created.
       * @param {jQuery.Event} e
       * @param {Aloha.Editable} editable
       */
      onEditableCreated: function (e, editable) {
        if (editable.obj.is('#contenteditor')) {
          editable.obj[0].addEventListener("keyup", icejsPlugin.onKeyUp);
        }
      },

      /**
       * Called on key up.
       */
      onKeyUp: function (e) {
        if (activateTrackingOnKeyUp && e.keyCode === 8) {
          booktype.tracker.enableChangeTracking();
          icejsPlugin.registerEventHandlers();
          activateTrackingOnKeyUp = false;
        }
        return true;
      },

      makeClean: function (obj) {
        jQuery(obj).find('span.del, span.ins').each(function () {
          var $elem = jQuery(this);

          // first, replace &nbsp; with real white spaces
          $elem.html($elem.html().replace(/&nbsp;/gi, ' '));
        });
      }
    });

    icejsPlugin.trackAndReplace = function ($node, replace) {
      var $parent = $node.parent();

      var textNode = document.createTextNode($node.text());
      var replaceTextNode = document.createTextNode(replace);

      var insertNode = booktype.tracker.createIceNode('insertType', replaceTextNode);
      var deleteNode = booktype.tracker.createIceNode('deleteType', textNode);

      // if node's parent is a del tracking tag, treat it special
      if ($parent.is('span.del')) {

        // change text if next tag is insert tracking tag
        if ($parent.next().is('span.ins')) $parent.next().remove();
        $parent.after(insertNode);
        return true;
      }

      // if node's parent is a ins tracking tag, just replace text
      if ($parent.is('span.ins')) {
        if ($node.text().length < $parent.text().length) {
          $node.replaceWith(replace);
          return true;
        }

        $parent.html(replace);
        return true;
      }

      $node.after(insertNode);
      $node.after(deleteNode);
      $node.remove();
    };

    icejsPlugin.trackToolbarAction = function (data) {
      function trackFormatting(selectionTree) {
        for (var i = 0; i < selectionTree.length; i++) {
          var formatTag = jQuery('<' + actionTag + '>'),
            insertNode,
            deleteNode;

          var el = selectionTree[i];

          if (el.children.length > 0) {
            trackFormatting(el.children);
          } else {

            // skip empty text nodes
            if (el.domobj && el.domobj.nodeType === 3 && jQuery.trim(el.domobj.nodeValue).length === 0)
              continue;

            // also skip nodes with selection as none
            if (el.domobj && el.selection === 'none')
              continue;

            // convert domobj into jquery object to be reused
            var $node = jQuery(el.domobj);
            if (el.domobj && el.selection === 'full' && !($node.is('span.del, span.ins') || $node.parents().is('span.del, span.ins'))) {

              // check if current el can be wrapped by tracking tag
              if ((el.domobj.nodeType === 3 || Selection.canTag1WrapTag2('span', el.domobj.tagName)) && jQuery.trim(el.domobj.nodeValue).length > 0) {
                if (actionState) { // means applying format
                  insertNode = formatTag.html($node.clone())[0];
                  deleteNode = $node.clone()[0];
                } else { // means removing format
                  insertNode = $node.clone()[0];
                  deleteNode = formatTag.html($node.clone())[0];
                }

                var insertNode = booktype.tracker.createIceNode('insertType', insertNode);
                $node.after(insertNode);

                var deleteNode = booktype.tracker.createIceNode('deleteType', deleteNode);
                $node.before(deleteNode);

                if ($node.parent().is(actionTag)) $node.unwrap();
                $node.remove();
              } else if (el.domobj.nodeType === 1) {
                // nothing to do here. has no children, also no content i guess
                continue;
              } else {
                // console.log('weird elem? ', el.domobj.nodeValue);
              }
            } else if (el.domobj && el.selection === 'partial') {
              var formatTag = jQuery('<' + actionTag + '>'),
                preText = el.domobj.data.substr(0, el.startOffset),
                middleText = el.domobj.data.substr(el.startOffset, el.endOffset - el.startOffset),
                postText = el.domobj.data.substr(el.endOffset, el.domobj.data.length - el.endOffset);

              if (actionState) {
                insertNode = formatTag.html(middleText)[0];
                deleteNode = document.createTextNode(middleText);
              } else {
                insertNode = document.createTextNode(middleText);
                deleteNode = formatTag.html(middleText)[0];
              }

              var insertNode = booktype.tracker.createIceNode('insertType', insertNode);
              var deleteNode = booktype.tracker.createIceNode('deleteType', deleteNode);
              $.each([postText, insertNode, deleteNode, preText], function (id, domNode) {
                $node.after(domNode);
              });
              $node.remove();
            }
          }
        }
      }

      var actionTagsMap = {
        'bold': 'b',
        'italic': 'i',
        'underline': 'u'
      };
      var trackedActions = jQuery.map(actionTagsMap, function (elem, key) { return key; });
      var shouldTrackAction = (data.action !== undefined && trackedActions.indexOf(data.action) > -1);
      var range = Selection.getRangeObject();

      if (shouldTrackAction && booktype.tracker.isTracking) {
        var actionTag = actionTagsMap[data.action];
        var selectionTree = range.getSelectionTree();
        var actionState = Aloha.queryCommandState(data.action);

        trackFormatting(selectionTree);
      }
    };

    icejsPlugin.checkFormattingButtons = function (rangeObject) {
      if (!booktype.tracker || (booktype.tracker && !booktype.tracker.isTracking)) {
        return;
      }

      var isDeleteTrackingInTree = function (selectionTree) {
        for (var i = 0; i < selectionTree.length; i++) {
          var el = selectionTree[i];

          var $node = jQuery(el.domobj);
          if (el.domobj && el.selection !== 'none' && ($node.is('span.del') || $node.parent().is('span.del'))) {
            return true;
          } else if (el.children.length > 0) {
            if (isDeleteTrackingInTree(el.children))
              return true;
            continue;
          } else {
            continue;
          }
          continue;
        }
        return false;
      };

      // really this is stupid
      setTimeout(function () {
        var selectionTree = Aloha.Selection.getSelectionTree(rangeObject);
        var disableFormattingButtons = isDeleteTrackingInTree(selectionTree);
        var formattingButtons = jQuery('.btn-group.formatting, .btn-group.fonts, .btn-group.fontsize, .btn-group.color').children('button');

        if (disableFormattingButtons) {
          formattingButtons.addClass('disabled');
        } else {
          formattingButtons.removeClass('disabled');
        }
      }, 100);
    };

    return icejsPlugin;
  }
);