define(['aloha', 'aloha/plugin', 'jquery', 'ui/ui', 'booktype'],
  function (Aloha, Plugin, jQuery, UI, booktype) {
    'use strict';

    return Plugin.create('import', {
      init: function () {
        // after changing the file, the form will auto trigger the import
        // we need to set the callback to the uploadDocxForm
        window.uploadCallback = function (response) {
          Aloha.getEditableById('contenteditor').setContents(response.new_content);
          Aloha.trigger('aloha-my-undo', {'editable': Aloha.getEditableById('contenteditor')});

          // let's remove the callback to avoid issues somewhere else
          var uploadDocxForm = jQuery('#uploadDocxForm');
          uploadDocxForm.removeAttr('data-upload-callback');
        };

        var openFileDialog = function () {
          var chapterId = booktype.editor.getCurrentChapterID();
          var importMode = 'append';
          var uploadDocxForm = jQuery('#uploadDocxForm');
          var actionUrl = uploadDocxForm.data('action');

          actionUrl = actionUrl.replace('chapter-pk-to-replace', chapterId);
          uploadDocxForm.attr('data-upload-callback', 'uploadCallback');
          uploadDocxForm.attr('action', actionUrl);
          uploadDocxForm.find('input[name=import_mode]').val(importMode)
          uploadDocxForm.find('input[type=file]')
            .val('')
            .trigger("click");
        };

        // we should discuss if create buttons inside plugins instead of writing html
        // inside aloha_menu.html
        UI.adopt('docximport', null, {
          click: function () {
            openFileDialog();
          }
        });

        // NOTE: we could later add more options of importing here
      }
    });
  });
