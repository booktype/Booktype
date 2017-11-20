define(['aloha', 'aloha/plugin', 'jquery', 'ui/ui', 'PubSub', 'booktype', 'aloha/console', 'aloha/ephemera', 'underscore'],
  function (Aloha, Plugin, jQuery, UI, PubSub, booktype, Console, Ephemera, _) {

    var editable = null;
    var range = null;
    var spanTitle = booktype._('non_breaking_space', 'Non breaking space');

    var _init = function (editable, unmodify) {
      editable.obj.find("*").each(function () {
        var $this = jQuery(this);

        if ($this.text().indexOf('\u00a0') !== -1) {
          $this.html($this.html().replace(/&nbsp;/gi, '<span title="' + spanTitle + '" class="nbsp">&nbsp;</span>'));

        }
      });
    };

    return Plugin.create('nbsp', {
      init: function () {
        // insert toolbar onclick handler
        UI.adopt('nbsp', null, {
          click: function (evt) {
            editable = Aloha.activeEditable;
            range = Aloha.Selection.getRangeObject();

            var $container = jQuery(range.commonAncestorContainer);

            if ($container.is('span.nbsp')) {
              $container.replaceWith(' ');
            } else {
              var $a = jQuery('<span title="' + spanTitle + '" class="nbsp">&nbsp;</span>');
              GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
              range.select();
            }
            booktype.editor.edit.disableSave(false);
          }
        });

        Aloha.bind('aloha-my-undo', function (event, args) {
          _init(args.editable, false);
        });

        Aloha.bind('aloha-editable-created', function ($event, editable) {
          _init(editable, true);
        });

        PubSub.sub('aloha.selection.context-change', function (evt) {
          // Check if there is no paragraph in the main editor. Create one if it is missing.
          var $editor = Aloha.getEditableById('contenteditor');
          var $el = jQuery(evt.range.commonAncestorContainer);

          // startOffset
          if ($el.hasClass('nbsp')) {
            jQuery('div.contentHeader a.action.nbsp').parent().addClass('disabled')

          } else {
            jQuery('div.contentHeader a.action.nbsp').parent().removeClass('disabled');
          }

          $editor.obj.find('span.nbsp').each(function (idx, e) {
            var $e = jQuery(e);
            if ($e.html() !== '&nbsp;') {
              $e.html('&nbsp;');
            }
          });
        });

      },
      makeClean: function (obj) {
        jQuery(obj).find('span.nbsp').each(function () {
          jQuery(this).replaceWith('\u00a0');
        });
      }
    });
  }
);