define([
    'aloha',
    'aloha/plugin',
    'aloha/selection',
    'PubSub',
    'ui/ui',
    'jquery19',
    'booktype',
    'react',
    'react-dom',
    'jsx!comments/components',
    'css!comments/css/comments'
  ],
  function (Aloha, Plugin, Selection, PubSub, UI, jQuery, booktype, React, ReactDOM, comps) {
    'use strict';

    var commentsPlugin = Plugin.create('comments', {
      defaultSettings: {
        enabled: true
      },

      init: function () {
        var plugin = this;

        plugin.settings = jQuery.extend(true, plugin.defaultSettings, plugin.settings);

        if (!plugin.settings.enabled)
          return;

        // listen to desired events :)
        plugin.bindEvents();

        UI.adopt('comment-insert', null, {
          click: function () {
            var editable = Aloha.activeEditable;
            var range = Selection.getRangeObject();

            plugin.insertCommentModal.show(
              range, editable, plugin._handleBubbleClick);
          }
        });
      },

      bindEvents: function () {
        var $document = jQuery(document);
        var plugin = this;

        // render components or not according to current activated panel
        $document.on('booktype-ui-panel-active', function (event, name) {
          if (name === 'edit')
            plugin.renderComponents();
          else
            plugin.unmountComponents();
        });

        // bind aloha selection change to enable or disable
        // insert comment option in aloha toolbar menu
        Aloha.bind('aloha-selection-changed', function () {
          var selectedText = Aloha.Markup.getSelectedText();
          var insertCommentOption = jQuery('a.action.comment-insert').parent();
          var noCommentsBtn = jQuery('.comments-content .no-comments-yet-btn');

          if (selectedText && selectedText.length > 0) {
            insertCommentOption.removeClass('disabled');
            noCommentsBtn.removeClass('disabled');
          }
          else {
            insertCommentOption.addClass('disabled');
            noCommentsBtn.addClass('disabled');
          }
        });

        // bind existent comment references in chapter content
        // with the corresponding click action
        Aloha.bind('aloha-editable-created', function (event, editable) {
          var bubbles = editable.obj.find('a.comment-link');
          bubbles.attr('contenteditable', false);
          bubbles.on('click', plugin._handleBubbleClick);

          // clean any selected bubble when first loading
          plugin._cleanSelectedBubble();
        });
      },

      renderComponents: function () {
        var plugin = this;

        // just in case
        plugin.cleanCommentsTab();

        var mountPoint = document.getElementById('commentsTab');
        var commentsTab = booktype.editor.createRightTab(
          'comments-tab', 'big-icon-comments', booktype._('comments', 'Chapter Comments'));

        var commentModal = React.createElement(comps.InsertCommentModal, {});
        plugin.insertCommentModal = ReactDOM.render(commentModal, document.getElementById('commentsModal'));

        var commentsComponent = React.createElement(comps.CommentList);
        ReactDOM.render(commentsComponent, mountPoint);

        // now trigger to pull latest comments and mount main component
        PubSub.pub('booktype-pull-latest-comments');

        commentsTab.onDeactivate = function () {
          plugin._cleanSelectedBubble();
          jQuery('#commentsTab .comment-box').removeClass('selected');
        };

        commentsTab.onActivate = function () {
        };

        booktype.editor.activateTabs([commentsTab]);
      },

      unmountComponents: function () {
        var mountPoint = document.getElementById('commentsTab');
        var modalMountPoint = document.getElementById('commentsModal');

        // we should unmount the components to avoid memory leaks
        ReactDOM.unmountComponentAtNode(mountPoint);
        ReactDOM.unmountComponentAtNode(modalMountPoint);

        this.cleanCommentsTab();
      },

      cleanCommentsTab: function () {
        // removes any created tab to avoid double buttons in side panel
        jQuery('div.right-tablist ul.navigation-tabs #comments-tab').remove();
      },

      _handleBubbleClick: function () {
        var plugin = commentsPlugin;
        var thisBubble = jQuery(this);
        var commentsTabBtn = jQuery('#comments-tab');
        var commentId = thisBubble.attr('id').substr(11);

        if (!commentsTabBtn.parent().hasClass('active')) {
          commentsTabBtn.trigger('click');

          setTimeout(function () {
            var top = thisBubble.offset().top - jQuery('#contenteditor').offset().top;
            jQuery(window).scrollTop(top - 100);
          }, 200);
        }

        plugin._cleanSelectedBubble();
        thisBubble.addClass('comment-selected');
        PubSub.pub('booktype-comment-bubble-selected', {cid: commentId});

        return false;
      },

      _cleanSelectedBubble: function () {
        jQuery('#contenteditor a.comment-link').removeClass('comment-selected');
      }
    });

    return commentsPlugin;
  }
);
