define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'underscore', 'PubSub', 'imageeditor/bk-image-editor'],
  function (Aloha, Plugin, jQuery, jQuery19, _, PubSub, BkImageEditor) {

    var BkImageEditorInstance = null;

    var isHistoryTabOpened = false;

    var enableSaveButton = function () {
      jQuery('#button-save').removeAttr('disabled');
      jQuery('#button-save-toggle').removeAttr('disabled');
    };

    var scaleImages = function ($container, toWidth) {
      // because it's wrong
      if (toWidth <= 0) return;

      BkImageEditor.scaleImages($container, toWidth);

      if (BkImageEditorInstance) {
        var transformData = BkImageEditorInstance.$image.attr('transform-data');
        transformData = JSON.parse(transformData);

        BkImageEditorInstance.editorWidth = transformData['editorWidth'];
        BkImageEditorInstance.imageWidth = transformData['imageWidth'];
        BkImageEditorInstance.imageHeight = transformData['imageHeight'];
        BkImageEditorInstance.imageTranslateX = transformData['imageTranslateX'];
        BkImageEditorInstance.imageTranslateY = transformData['imageTranslateY'];
        BkImageEditorInstance.frameWidth = transformData['frameWidth'];
        BkImageEditorInstance.frameHeight = transformData['frameHeight'];
        BkImageEditorInstance.FRAME_MAX_WIDTH = transformData['editorWidth'];
      }

      jQuery('div.group_img div.image', $container).each(function () {
        var $image = jQuery(this).find('img');
        var transformData = $image.attr('transform-data');

        if (!_.isUndefined(transformData)) {

          transformData = JSON.parse(transformData);

          // update image editor instance internal properties
          if (BkImageEditorInstance && BkImageEditorInstance.image === $image[0]) {
            BkImageEditorInstance.editorWidth = transformData['editorWidth'];
            BkImageEditorInstance.imageWidth = transformData['imageWidth'];
            BkImageEditorInstance.imageHeight = transformData['imageHeight'];
            BkImageEditorInstance.imageTranslateX = transformData['imageTranslateX'];
            BkImageEditorInstance.imageTranslateY = transformData['imageTranslateY'];
            BkImageEditorInstance.frameWidth = transformData['frameWidth'];
            BkImageEditorInstance.frameHeight = transformData['frameHeight'];
            BkImageEditorInstance.FRAME_MAX_WIDTH = transformData['editorWidth'];
          }
        }
      });

    };

    return Plugin.create('imageeditor', {
      makeClean: function (obj) {

        // remove imageEditor related class
        jQuery(obj).find('.bk-image-editor-frame').each(function () {
          var $div = jQuery(this);
          $div.removeClass('bk-image-editor-frame');
        });

        jQuery(obj).find('.bk-image-editor-image').each(function () {
          var $div = jQuery(this);
          $div.removeClass('bk-image-editor-image');
        });

        // scale all images
        scaleImages(jQuery(obj), 898);

      },
      init: function () {

        ////////////////
        // start edit //
        ////////////////
        PubSub.sub('bk-image-editor.start', function (message) {
          // try to stop previous editing
          try {
            BkImageEditorInstance.stop();
          } catch (err) {}

          BkImageEditorInstance = new BkImageEditor.BkImageEditor(
            message.image,
            message.frame,
            jQuery('#contenteditor').width()
          );
          BkImageEditorInstance.start();

          // temporary remove class from block to prevent cursor's style overriding
          BkImageEditorInstance.$frame.parent().removeClass('aloha-block');

          // catch mouseup event and dispatch new one for stop dropping image
          message.image.addEventListener("mouseup", function (event) {
            try {
              var myEvt = new MouseEvent('blur', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: event.clientX,
                clientY: event.clientY
              });
            } catch (err) {
              myEvt = document.createEvent('MouseEvents');
              myEvt.initMouseEvent('blur', true, true, window, 0,
                event.clientX, event.clientY,
                event.clientX, event.clientY,
                false, false, false, false, 0, null);
            }
            document.dispatchEvent(myEvt);
          });

        });

        ///////////////
        // stop edit //
        ///////////////
        PubSub.sub('bk-image-editor.stop', function (message) {
          try {
            BkImageEditorInstance.stop();
          } catch (err) {}

          BkImageEditorInstance.$frame.parent().addClass('aloha-block');
          BkImageEditorInstance = null;
        });

        /////////////
        // actions //
        /////////////
        PubSub.sub('bk-image-editor.action', function (message) {

          switch (message.action) {
            case 'flip_horizontal':
              BkImageEditorInstance.imageActions.flipHorizontal();
              break;

            case 'flip_vertical':
              BkImageEditorInstance.imageActions.flipVertical();
              break;

            case 'rotate_right':
              BkImageEditorInstance.imageActions.rotateRight();
              break;

            case 'rotate_left':
              BkImageEditorInstance.imageActions.rotateLeft();
              break;

            case 'toggle_fpi':
              BkImageEditorInstance.imageActions.toggleFPI();
              break;

            case 'zoom':
              BkImageEditorInstance.imageActions.zoom(message.value);
              break;

            case 'contrast':
              BkImageEditorInstance.imageActions.contrast(message.value);
              break;

            case 'brightness':
              BkImageEditorInstance.imageActions.brightness(message.value);
              break;

            case 'blur':
              BkImageEditorInstance.imageActions.blur(message.value);
              break;

            case 'saturate':
              BkImageEditorInstance.imageActions.saturate(message.value);
              break;

            case 'opacity':
              BkImageEditorInstance.imageActions.opacity(message.value);
              break;
          }

        });

        // enable save button and dropdown with options
        PubSub.sub('bk-image-editor.transform-data.updated', function (message) {
          enableSaveButton();
        });

        // image inserted -> trigger rescale images
        PubSub.sub('imagesimple.image.inserted', function (message) {
          var $editable = Aloha.getEditableById('contenteditor');
          if (!$editable) return;

          scaleImages($editable.obj, jQuery('#contenteditor').width());
        });

        // bk-image-editor.frame.changed -> update caption container
        PubSub.sub('bk-image-editor.frame.changed', function (message) {

          if (BkImageEditorInstance) {
            BkImageEditorInstance.$frame.parent().find('div.caption_small').width(message.x);
          }

        });

        // chapter history revision reverted ->
        Aloha.bind('editor.chapter_history.revert_revision', function (message) {
          isHistoryTabOpened = false;
        });

        // chapter history diff displayed -> trigger rescale images
        Aloha.bind('editor.chapter_history.chapter_diff', function (message) {
          var _contentrevision = jQuery('#contentrevision');
          scaleImages(_contentrevision, _contentrevision.width());
        });

        // chapter history diff displayed -> trigger rescale images
        Aloha.bind('editor.chapter_history.history_loaded', function (message) {
          var _contentrevision = jQuery('#contentrevision');
          scaleImages(_contentrevision, _contentrevision.width());
        });

        // aloha editor initialized -> trigger rescale images
        Aloha.bind('aloha-editable-created', function ($event, editable) {
          if (editable.obj && editable.obj.attr('id') == 'contenteditor') {

            // this is kinda tricky
            jQuery('div.group_img div.image', editable.obj).each(function () {
              var $image = jQuery(this).find('img');
              $image.load(function () {
                scaleImages(editable.obj, jQuery('#contenteditor').width());
              });
            });

          }
        });

        // undo/redo -> trigger rescale images
        Aloha.bind('aloha-my-undo', function (event, args) {
          var $editable = Aloha.getEditableById('contenteditor');
          if (!$editable) return;

          scaleImages($editable.obj, jQuery('#contenteditor').width());
        });

        // window resize -> trigger rescale images
        jQuery(window).resize(function () {
          var $editable = Aloha.getEditableById('contenteditor');
          if (!$editable) return;

          if (isHistoryTabOpened) {
            var _contentrevision = jQuery('#contentrevision');
            scaleImages(_contentrevision, _contentrevision.width());
          } else {
            scaleImages($editable.obj, jQuery('#contenteditor').width());
          }
        });

        // tab opened -> trigger rescale images
        jQuery19(document).on('booktype-tab-activate', function (event, extraParams) {
          if (window.booktype.editor.data.activePanel.name !== 'edit') return;

          if (extraParams['tabID'] === 'history-tab') {
            isHistoryTabOpened = true;
            var _contentrevision = jQuery('#contentrevision');
            scaleImages(_contentrevision, _contentrevision.width());
          } else {
            isHistoryTabOpened = false;
            var $editable = Aloha.getEditableById('contenteditor');
            if (!$editable) return;
            scaleImages($editable.obj, jQuery('#contenteditor').width());
          }
        });

        // tab closed -> trigger rescale images
        jQuery19(document).on('booktype-tab-deactivate', function (event, extraParams) {
          isHistoryTabOpened = false;

          if (window.booktype.editor.data.activePanel.name !== 'edit') return;
          if (extraParams['tabID'] === 'history-tab') return;

          var $editable = Aloha.getEditableById('contenteditor');
          if (!$editable) return;

          scaleImages($editable.obj, jQuery('#contenteditor').width());
        });


      }
    });

  }
);
