define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'booktype'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, booktype) {
    'use strict';

    return Plugin.create('wcount', {
      init: function () {
        var getDataFromServer = function () {
          var chapterId = booktype.editor.getCurrentChapterID();
          booktype.sendToCurrentBook({
              'command': 'word_count',
              'current_chapter_id': chapterId,
              'current_chapter_content': Aloha.getEditableById('contenteditor').getContents()
            },
            function (data) {
              var $container = jQuery19('#elCount .modal-dialog .modal-content .modal-body'),
                chapter = data['current_chapter'];

              // set whole book values
              $container.find('.all_wcount').text(data.wcount);
              $container.find('.all_charcount').text(data.charcount);
              $container.find('.all_charspacecount').text(data.charspacecount);

              // set current chapter values
              $container.find('.wcount').text(chapter.wcount);
              $container.find('.charcount').text(chapter.charcount);
              $container.find('.charspacecount').text(chapter.charspacecount);
            }
          );
        };

        var cleanCounters = function () {
          var $container = jQuery19('#elCount .modal-dialog .modal-content .modal-body');
          $container.find('span').html('-');
        };

        UI.adopt('wcount', null, {
          click: function () {
            cleanCounters();
            getDataFromServer();
            jQuery19('#elCount').modal('show');
          }
        });
      }
    });
  });