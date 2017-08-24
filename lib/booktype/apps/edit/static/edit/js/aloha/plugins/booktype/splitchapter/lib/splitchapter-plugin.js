define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'toolbar/toolbar-plugin', 'underscore', 'booktype'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, block, BlockManager, toolbar, _, booktype) {

    var textForSplitting = '';

    var removeClasses = function (node) {
      node.find('.aloha-split-chapter').each(function (idx, $elem) {
        if ($elem)
          jQuery($elem).removeClass('aloha-split-chapter');
      });
    };

    var toHTML = function () {
      var output = '';
      var isIn = false;

      var $content = jQuery('#contenteditor').clone();
      $content.html(Aloha.getEditableById('contenteditor').getContents());

      $content.children().each(function () {
        var $item = jQuery(this);

        if ($item.hasClass('aloha-split-chapter')) { isIn = true; }

        if (isIn) {
          $item.removeClass('aloha-split-chapter');
          output += $item[0].outerHTML;
        }
      });

      return output;
    };

    var getParent = function (node) {
      if (node.parent().attr("id") === "contenteditor") {
        return node;
      }

      return getParent(node.parent());
    };

    var getPossibleName = function (node) {
      var headers = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
      var _modifyName = function (text) {
        if (text) {
          text = _.str.capitalize(_.str.clean(_.trim(text)));

          if (text.length > 100) {
            return _.prune(text, 100);
          }

          return text;
        }
        return '';
      };

      for (var i = 0; i < headers.length; i++) {
        var $possible = node.closest(headers[i]);

        if ($possible.length > 0) {
          return _modifyName($possible.text());
        }
      }

      return _modifyName(node.text());
    };

    return Plugin.create('splitchapter', {
      init: function () {

        var $dialog = jQuery19("#splitChapter");

        $dialog.find('.operation-split').on('click', function () {
          var current_chapter_id = booktype.editor.getCurrentChapterID();
          var chapterTitle = $dialog.find('input[name=chapter]').val();

          if (_.trim(chapterTitle) !== '') {
            // send to channel
            booktype.sendToCurrentBook(
              {
                "command": "split_chapter",
                "content": textForSplitting,
                "title": chapterTitle,
                "chapterID": current_chapter_id
              },
              function (data) {
                if (data.result) {
                  var isIn = false;

                  jQuery('#contenteditor').children().each(function () {
                    var $item = jQuery(this);

                    if ($item.hasClass('aloha-split-chapter')) {
                      isIn = true;
                    }
                    if (isIn) { $item.remove(); }
                  });

                  booktype.editor.data.chapters.clear();
                  booktype.editor.data.chapters.loadFromArray(data.chapters);
                  booktype.editor.data.holdChapters.clear();
                  booktype.editor.data.holdChapters.loadFromArray(data.hold);
                  booktype.editor.toc.redraw();
                  booktype.editor.edit.saveContent();
                  $dialog.modal('hide');
                } else if (data.reason){
                  jQuery('.alert', $dialog).html(data.reason);
                  jQuery('.alert', $dialog).removeClass('hide');
                } else {
                  // remove split classes anyway
                  removeClasses(jQuery('#contenteditor'));
                  $dialog.modal('hide');
                }

              }
            );
          }
        });

        $dialog.on('hidden.bs.modal', function () {
          removeClasses(jQuery('#contenteditor'));
        });

        $dialog.on('shown.bs.modal', function () {
          $dialog.find('input[name=chapter]').focus();
        });

        UI.adopt('split-chapter', null, {
          click: function () {
            if (jQuery('#contenteditor').find('div.aloha-block-EndnoteBlock').length) {
              var msg = booktype._('split_chapter_error', 'At the moment we do not allow splitting of chapters with endnotes.');
              alert(msg);
              return;
            }

            var currentSelection = Aloha.Selection.getRangeObject(),
                $parent = getParent(jQuery(currentSelection.startContainer));

            var possibleName = getPossibleName(jQuery(currentSelection.startContainer));

            $parent.addClass('aloha-split-chapter');
            textForSplitting = toHTML();
            $dialog.find('input[name=chapter]').val(possibleName);
            jQuery('.alert', $dialog).addClass('hide');
            $dialog.modal('show');
          }
        });

        Aloha.bind('aloha-selection-changed', function (event, rangeObject) {
          if (Aloha.activeEditable) {
            rangeObject.findMarkup(function () {
              var tagName = this.tagName.toLowerCase();
              if (tagName === 'div' && !jQuery(this).is("#contenteditor")) {
                toolbar.disableMenu('split-chapter');
                return true;
              } else if (tagName === 'div' && jQuery(this).is("#contenteditor")) {
                toolbar.enableMenu('split-chapter');
                return true;
              } else {
                toolbar.enableMenu('split-chapter');
              }
            });
          }
        });

      },

      makeClean: function (obj) {

      }
    });
  }
);
