define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block',
    'block/blockmanager', 'booktype', 'underscore', 'PubSub', 'image/image-plugin', 'imagesimple/image-block'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Console, Ephemera, block, BlockManager, booktype, _, PubSub,
            image, ImageBlock) {
    var editable;
    var range;
    var fileUpload;

    // Image Manager Dialog
    var $manager = null;

    // Popup window when image is selected in the editor
    var $popup = null;

    // Loaded attachments for this book
    var attachments = null;

    // Image selected in the dialog
    var selectedImage = null;

    // This is just one big dirty hack
    // Should really figure out how to avoid this situation
    var doNothing = false;

    // Reference to image selected in the editor
    var $imageInFocus = null;

    // boolean, shows whether image is under editing at the moment
    var isImageUnderEdit = null;

    // Get attachment
    var getAttachment = function (mediaID) {
      return _.find(attachments, function (a) {
        return a.id === _.toNumber(mediaID);
      });
    };

    // Image is selected in the editor
    var selectImage = function ($img) {

      if (!isImageUnderEdit) {
        var pos = $img.closest('div.group_img').offset();
        var y = pos.top;

        $popup.css('top', y - 40);
        $popup.css('left', pos.left);

        jQuery('.bk-image-editor-stop, .bk-image-editor-ui-controls', $popup).hide();

        $popup.show();

        // remove border from last image in focus
        if ($imageInFocus) {
          $imageInFocus.parent().removeClass('image-focus');
        }

        $imageInFocus = $img;

        // add border to the frame
        $imageInFocus.parent().addClass('image-focus');
      }

      // reset selection
      // this will help not to loose focuse in case if we want to change image align
      range = Aloha.Selection.getRangeObject();
      if (window.getSelection) {
        // Chrome
        if (window.getSelection().empty) {
          window.getSelection().empty();
        }
        // Firefox
        else if (window.getSelection().removeAllRanges) {
          window.getSelection().removeAllRanges();
        }
      }
      // IE
      else if (document.selection) {
        document.selection.empty();
      }

      // notify all subscribers that image was selected in the editor
      PubSub.pub('imagesimple.image.selected', {'image': $img});

    };

    var reloadAttachments = function (callback) {
      booktype.sendToCurrentBook(
        {
          'command': 'attachments_list',
          'options': {
            'width': 150,
            'height': 150,
            'aspect_ratio': true
          }
        },
        function (data) {
          attachments = data.attachments;
          showImages(data.attachments);

          if (!_.isUndefined(callback)) {
            callback();
          }
        });
    };

    // Show images in the Image Manager Dialog
    var showImages = function (attachments) {
      var $imageTemplate = _.template(jQuery19('#templateImageThumbnail').html());

      jQuery19('.uploads-grid', $manager).empty();

      _.each(attachments, function (att, i) {

        var $i = $imageTemplate(
          {
            'name': att.name,
            'preview': att.preview,
            'media_id': att.id
          });

        jQuery19('.uploads-grid', $manager).append($i);
      });

      jQuery19('.uploads-grid li a.delete-attachment').on('click', function () {
        var $this = jQuery19(this);
        var mediaID = $this.parent().parent().parent().attr('data-media-id');

        jQuery19('#removeMedia INPUT[name=attachments]').val(mediaID);

        jQuery19('#removeMedia').modal('show');

        return false;
      });

      jQuery19('.uploads-grid li').click(function () {
        var mediaID = jQuery19(this).attr('data-media-id');

        if (_.isUndefined(mediaID)) {
          return;
        }

        var att = getAttachment(mediaID);

        selectedImage = att;

        jQuery19(this).closest('.tab-pane').addClass('open-info');
        jQuery19(this).parent().parent().find('ul li').removeClass('active');
        jQuery19(this).toggleClass('active');
        jQuery19('.image-info-container', $manager).removeClass('metadata-switch');

        // load image into the browser and only after insert it in the preview html
        // doing it in this way will position image more correctly
        var imgsrc = jQuery19(this).find('img').attr('data-src');
        var img = new Image();
        img.src = imgsrc;
        img.onload = function () {
          jQuery19('.image-preview img', $manager).attr('src', imgsrc);
          var imgHeight = jQuery19('.image-preview img', $manager).height();
          var imgMargin = Math.round((226 - imgHeight) / 2) + 'px';
          jQuery19('.image-preview img', $manager).css('margin-top', imgMargin);
        };

        var $t2 = _.template(jQuery19('#templateImageInfo').html());
        var d = '';

        if (att && att.dimension !== null) {
          d = att.dimension[0] + 'x' + att.dimension[1] + 'px';

        }

        var info = {
          'filesize': booktype.utils.formatSize(att.size),
          'name': att.name,
          'dimension': d,
          'timestamp': att.created
        };

        jQuery19('.image-info').html($t2(info));

        // Resize the grid
        var uplGridWidth = jQuery19('.tab-pane.active', $manager).width();
        var newGridWidth = Math.round(uplGridWidth - 320) + 'px';

        jQuery19('.open-info .uploads-grid', $manager).css('width', newGridWidth);
      });

      jQuery19('.uploads-grid > li').hover(
        function () {
          jQuery19(this).addClass('open-image-menu');
        },
        function () {
          jQuery19(this).removeClass('open-image-menu');
          jQuery19(this).removeClass('open');
        }
      );
    };

    /* Initialise all images */
    /* Create Aloha Block. Bind click event to all images */
    var _initImages = function (editable) {
      jQuery('img', editable.obj).each(function () {

        var $img = jQuery(this);

        // wrap image tag with required wrappers
        var $divImage = $img.closest('div.image');
        var $groupImg = $img.closest('div.group_img');

        if ($divImage.length === 0) {
          $img.wrap(jQuery('<div/>', {class: 'image'}));
        }

        if ($groupImg.length === 0) {
          $img.parent().wrap(jQuery('<div/>', {class: 'group_img'}));
        }

        $groupImg = $img.closest('div.group_img');

        $groupImg.find('div.image:first').mahalo();

        // create block
        $groupImg.alohaBlock({'aloha-block-type': 'ImageBlock'});
      });

      jQuery19('img', editable.obj).on('dblclick', function () {
        if (!isImageUnderEdit) {
          startEdit(this);
        }
      });
    };

    // TODO remove this after new UI
    var startEdit = function (img) {

      PubSub.sub('bk-image-editor.initialized', function (message) {
        // prepare sliders
        var currentZoomValue = message.imageEditor.imageWidth / (message.imageEditor.imageRawWidth / 100) - 100;
        currentZoomValue = parseInt(currentZoomValue.toFixed());

        jQuery19('input[bk-image-editor-action="toggle_fpi"]').prop('checked', message.imageEditor.frameFPI).change();
        jQuery19('#bk-image-editor-zoom-slider').data('slider').setValue(currentZoomValue);
        jQuery19('#bk-image-editor-contrast-slider').data('slider').setValue(message.imageEditor.imageContrast);
        jQuery19('#bk-image-editor-brightness-slider').data('slider').setValue(message.imageEditor.imageBrightness);
        jQuery19('#bk-image-editor-blur-slider').data('slider').setValue(message.imageEditor.imageBlur * 100);
        jQuery19('#bk-image-editor-saturate-slider').data('slider').setValue(message.imageEditor.imageSaturate);
        //jQuery19('#image-opacity-slider').data('slider').setValue(message.imageEditor.imageOpacity);

      });

      PubSub.pub('bk-image-editor.start', {
        'image': img,
        'frame': jQuery(img).parent('div.image')[0]
      });

      jQuery('.bk-image-editor-stop, .bk-image-editor-ui-controls', $popup).show();
      jQuery('.bk-image-editor-start', $popup).hide();
      $popup.css('top', parseInt($popup.css('top')) - 255);
      isImageUnderEdit = true;
    };

    var stopEdit = function () {
      PubSub.pub('bk-image-editor.stop', {});

      jQuery('.bk-image-editor-stop, .bk-image-editor-ui-controls', $popup).hide();
      jQuery('.bk-image-editor-start', $popup).show();
      $popup.css('top', parseInt($popup.css('top')) + 255);
      isImageUnderEdit = false;
    };

    return Plugin.create('imagesimple', {
      makeClean: function (obj) {

        jQuery(obj).find('DIV.group_img').each(function () {
          var $groupImg = jQuery(this);

          // create new group_img
          var $newGroupImg = jQuery('<div class="group_img"></div>');
          $newGroupImg.css('text-align', $groupImg.css('text-align'));
          $newGroupImg.append($groupImg.find('div.image'));

          // find caption if it exists
          var $divCaptionSmall = $groupImg.find('div.caption_small');

          if ($divCaptionSmall.length > 0) {
            var $newCaptionSmall = jQuery('<div class="caption_small">' + $divCaptionSmall.html() + '</div>');
            $newGroupImg.append($newCaptionSmall);
          }

          // swap new group_img with new one
          $groupImg.replaceWith($newGroupImg);

        });

        jQuery(obj).find('.image-focus').each(function () {
          var $div = jQuery(this);
          $div.removeClass('image-focus');
        });

      },

      init: function () {
        $manager = jQuery19(document).find('#imageManager');
        $popup = jQuery19('#imagePopup');


        BlockManager.registerBlockType('ImageBlock', ImageBlock.ImageBlock);
        var alertWrapper = jQuery19('.alert-wrapper');

        $(document).bind('drop dragover dragenter', function (e) {
          e.preventDefault();
        });

        jQuery19('.upload-file', $manager).fileupload({
          dataType: 'json',
          sequentialUploads: true,
          dropZone: jQuery19('#imageManager .drag-area'),
          pasteZone: jQuery19('#imageManager .drag-area'),
          done: function (e, data) {
            reloadAttachments(function () {
              jQuery19('a.medialibrary', $manager).tab('show');
            });

            jQuery19('.upload-file', $manager).prop('disabled', false);
            jQuery19(document).trigger('booktype-attachment-uploaded', [data.files]);

            alertWrapper.addClass('hidden');
          },
          add: function (e, data) {

            var fileName = null;

            if (!_.isUndefined(data.files[0])) {
              fileName = data.files[0].name;
            }

            if (fileName) {
              if (window.booktype.utils.isUploadAllowed(fileName)) {
                jQuery19('.upload-file', $manager).prop('disabled', true);
                alertWrapper.removeClass('hidden');
                data.formData = [{'name': 'clientID', 'value': window.booktype.clientID}];
                fileUpload = data.submit();
              } else {
                var $error = jQuery19('#uploadMediaError');
                $error.modal('show');
              }
            }
          }
        });

        jQuery19('.image-dropdown-button', $manager).click(function () {
          jQuery19(this).parent().toggleClass('open');
          return false;
        });

        jQuery19('a.closeinfo', $manager).click(function () {
          jQuery19(this).closest('.tab-pane').removeClass('open-info');
          jQuery19(this).parent().removeClass('metadata-switch');
          jQuery19('.uploads-grid').css('width', '');
        });


        jQuery19('a.metadata-btn', $manager).click(function () {
          jQuery19(this).parent().toggleClass('metadata-switch');
        });

        jQuery19('a.cancel-metadata-btn', $manager).click(function () {
          jQuery19(this).parent().toggleClass('metadata-switch');
        });

        jQuery19('.coverInfoButton', $manager).click(function () {
          jQuery19('.coverInfo').toggleClass('open');
        });

        jQuery19('.insert-image', $manager).on('click', function ($event) {
          var title = jQuery19.trim(jQuery19('input.image-title', $manager).val());
          var description = jQuery19.trim(jQuery19('textarea.image-description', $manager).val());

          var $image = jQuery('<img alt="" src=""/>').prop('src', 'static/' + selectedImage.name);
          $image.prop('alt', title);

          $image.on('click', function ($e) {
            var $img = jQuery19($e.target);
            selectImage($img);

            return true;
          });

          var $groupImg = jQuery('<div class="group_img"></div>');
          var $divImage = jQuery('<div class="image"></div>');

          $divImage.append($image);
          $groupImg.append($divImage);

          if (description !== '') {
            $groupImg.append(jQuery('<div class="caption_small">' + description + '</div>'));
          }

          // create aloha block with caption wrapper
          $groupImg.alohaBlock({'aloha-block-type': 'ImageBlock'});

          // Sometimes IE has issues with focus. In case when IE looses focus, this should
          // probably to the work
          var $editable = Aloha.getEditableById('contenteditor');
          GENTICS.Utils.Dom.insertIntoDOM($groupImg, range, $editable.obj);

          $manager.modal('hide');

          // publish message notification that toolbar action was triggered
          // used in undo plugin to make snapshot
          PubSub.pub('toolbar.action.triggered', {'event': $event});

          // notify that image was inserted into the editor
          PubSub.pub('imagesimple.image.inserted', {'image': $image});

          jQuery19($image).on('dblclick', function () {
            startEdit(this);
          });

        });

        $manager.on('hide.bs.modal', function () {
          jQuery19('#removeMedia .btn-primary').unbind('click.simpleimage');
        });

        $manager.on('show.bs.modal', function () {
          selectedImage = null;
          jQuery19('input.image-title', $manager).val('');
          jQuery19('textarea.image-description', $manager).val('');
          jQuery19('.image-info-container', $manager).removeClass('metadata-switch');
          jQuery19('#medialibrary').removeClass('open-info');
          jQuery19('a.medialibrary', $manager).tab('show');

          reloadAttachments();

          jQuery19('#removeMedia .btn-primary').bind('click.simpleimage', function () {
            if (jQuery19('#removeMedia INPUT[name=understand]:checked').val() === 'on') {
              var lst = jQuery19('#removeMedia INPUT[name=attachments]').attr('value').split(',');

              if (lst.length === 0) {
                return;
              }

              booktype.ui.notify(booktype._('removing_media_files', 'Removing media files'));

              booktype.sendToCurrentBook({
                  'command': 'attachments_delete',
                  'attachments': lst
                },
                function () {
                  booktype.ui.notify();
                  jQuery19('#removeMedia').modal('hide');
                  reloadAttachments();

                  jQuery19('#medialibrary').removeClass('open-info');

                  // Trigger event
                  jQuery19(document).trigger('booktype-attachment-deleted');
                });
            }

          });

        });

        // ImagePopup remove
        jQuery19('a.remove', $popup).on('click', function ($e) {
          // Is this image in a div ?
          if ($imageInFocus.parent() && $imageInFocus.parent().parent() && $imageInFocus.parent().parent().hasClass('group_img')) {
            $imageInFocus.closest('div.group_img').remove();
          } else {
            $imageInFocus.remove();
          }

          $e.stopPropagation();
          $e.preventDefault();
          $popup.hide();
          isImageUnderEdit = false;

          doNothing = true;

          // This is so stupid
          setTimeout(function () {
            doNothing = false;
          }, 100);

          // publish message notification that image was deleted
          PubSub.pub('toolbar.action.triggered', {'event': $e});
          return false;
        });

        // ImagePopup start edit
        jQuery19('a.bk-image-editor-start', $popup).on('click', function ($e) {
          startEdit($imageInFocus[0]);
          return false;
        });

        // ImagePopup stop edit
        jQuery19('a.bk-image-editor-stop', $popup).on('click', function ($e) {
          stopEdit();
          return false;
        });

        // ImagePopup actions
        jQuery('button.bk-image-editor-action, button.bk-image-editor-action li', $popup).on('click', function (event) {

          if (event.target.tagName === 'I') {
            event.target = event.target.parentElement;
          }

          PubSub.pub('bk-image-editor.action', {
            'action': event.target.getAttribute('bk-image-editor-action')
          });
        });

        // FPI checkbox
        jQuery('input.bk-image-editor-action', $popup).on('change', function (event) {
          if (event.target.tagName === 'I') {
            event.target = event.target.parentElement;
          }

          PubSub.pub('bk-image-editor.action', {
            'action': event.target.getAttribute('bk-image-editor-action')
          });
        });

        // ImagePopup zoom
        jQuery19('#bk-image-editor-zoom-slider').slider().on('slide', function () {
          PubSub.pub('bk-image-editor.action', {
            'action': 'zoom',
            'value': jQuery19(this).data('slider').getValue()
          });
          return false;
        });

        // ImagePopup contrast
        jQuery19('#bk-image-editor-contrast-slider').slider().on('slide', function () {
          PubSub.pub('bk-image-editor.action', {
            'action': 'contrast',
            'value': jQuery19(this).data('slider').getValue()
          });
          return false;
        });

        // ImagePopup brightness
        jQuery19('#bk-image-editor-brightness-slider').slider().on('slide', function () {
          PubSub.pub('bk-image-editor.action', {
            'action': 'brightness',
            'value': jQuery19(this).data('slider').getValue()
          });
          return false;
        });

        // ImagePopup blur
        jQuery19('#bk-image-editor-blur-slider').slider().on('slide', function () {
          PubSub.pub('bk-image-editor.action', {
            'action': 'blur',
            'value': jQuery19(this).data('slider').getValue()
          });
          return false;
        });

        // ImagePopup saturation
        jQuery19('#bk-image-editor-saturate-slider').slider().on('slide', function () {
          PubSub.pub('bk-image-editor.action', {
            'action': 'saturate',
            'value': jQuery19(this).data('slider').getValue()
          });
          return false;
        });

        // window resize -> update popup coordinates according to the image
        jQuery(window).resize(function () {
          if ($imageInFocus) {
            var pos = $imageInFocus.closest('div.group_img').offset();
            var y = pos.top;

            if (isImageUnderEdit) {
              $popup.css('top', y - 255 - 40);
            } else {
              $popup.css('top', y - 40);
            }

            $popup.css('left', pos.left);
          }
        });

        // tab opened -> update popup coordinates according to the image
        jQuery19(document).on('booktype-tab-activate', function (event, extraParams) {
          setTimeout(function () {
            if ($imageInFocus) {
              var pos = $imageInFocus.closest('div.group_img').offset();
              var y = pos.top;

              if (isImageUnderEdit) {
                $popup.css('top', y - 255 - 40);
              } else {
                $popup.css('top', y - 40);
              }
              $popup.css('left', pos.left);
            }
          }, 100);
        });

        // tab closed -> update popup coordinates according to the image
        jQuery19(document).on('booktype-tab-deactivate', function (event, extraParams) {
          setTimeout(function () {
            if ($imageInFocus) {
              var pos = $imageInFocus.closest('div.group_img').offset();
              var y = pos.top;

              if (isImageUnderEdit) {
                $popup.css('top', y - 255 - 40);
              } else {
                $popup.css('top', y - 40);
              }
              $popup.css('left', pos.left);
            }
          }, 100);
        });

        // chapter history revision reverted
        Aloha.bind('editor.chapter_history.revert_revision', function (message) {
          isImageUnderEdit = false;
          $popup.hide();
        });

        Aloha.bind('aloha-selection-changed', function (event, rangeObject, originalEvent) {
          if (doNothing) {
            return;
          }

          if (!isImageUnderEdit) {
            if ($popup.is(':visible')) {
              $popup.hide();
            }

            if ($imageInFocus) {
              $imageInFocus.parent().removeClass('image-focus');
              $imageInFocus = null;
            }
          }
        });

        Aloha.bind('aloha-image-selected', function (event) {
          selectImage(image.imageObj);

          doNothing = true;
          setTimeout(function () {
            doNothing = false;
          }, 100);

          return true;
        });

        // This is triggered after undo operation
        Aloha.bind('aloha-my-undo', function (event, args) {
          _initImages(args.editable);
        });

        // When Aloha editor is initialized just hook on every image in the editor
        Aloha.bind('aloha-editable-created', function ($event, editable) {
          // reset any image editor that was left open
          if (isImageUnderEdit) stopEdit();

          _initImages(editable);
        });

        Aloha.bind('aloha-editable-destroyed', function ($event, editable) {
          $popup.hide();
        });

        UI.adopt('insertImage', null, {
          click: function () {
            editable = Aloha.activeEditable;
            range = Aloha.Selection.getRangeObject();
            $manager.modal('show');
          }
        });
      }
    });
  }
);
