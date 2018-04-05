define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block',
    'block/blockmanager', 'booktype', 'underscore', 'PubSub', 'image/image-plugin', 'imagesimple/image-block',
    'imageeditor/bk-image-editor'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Console, Ephemera, block, BlockManager, booktype, _, PubSub,
            image, ImageBlock, BkImageEditor) {
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

    // boolean, shows whether image is under templating
    var isImageUnderTemplating = null;

    // Get attachment
    var getAttachment = function (mediaID) {
      return _.find(attachments, function (a) {
        return a.id === _.toNumber(mediaID);
      });
    };

    // Image is selected in the editor
    var selectImage = function ($img) {

      if (!isImageUnderEdit && !isImageUnderTemplating) {
        var pos = $img.closest('div.group_img').offset();
        var y = pos.top;

        $popup.css('top', y - 40);
        $popup.css('left', pos.left);

        jQuery(
          '.bk-image-editor-stop, ' +
          '.bk-image-layout-selected, ' +
          '.bk-image-editor-ui-controls, ' +
          '.bk-image-layout-ui-controls',
          $popup
        ).hide();

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
            'media_id': att.id,
            'dimension': att.dimension,
          });

        jQuery19('.uploads-grid', $manager).append($i);
      });

      jQuery19('.uploads-grid li a.rename-attachment').on('click', function () {
        var $this = jQuery19(this);
        var mediaID = $this.parent().parent().parent().attr('data-media-id');
        var filename = $this.parent().parent().parent().attr('data-filename');
        var splittedFilename = filename.split('.');

        jQuery19('#renameMedia INPUT[name=attachment]').val(mediaID);
        jQuery19('#renameMedia INPUT[name=filename]').val(splittedFilename.slice(0, -1).join('.'));
        jQuery19('#renameMedia form span').html(_.last(splittedFilename));
        jQuery19('#renameMedia').modal('show');
        var $alert = jQuery19('#renameMedia div.alert');
        $alert.addClass('hide');

        return false;
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

      jQuery19('#media-image-search input').trigger('keyup');

    };

    /* Initialise all images */
    /* Create Aloha Block. Bind click event to all images */
    var _initImages = function (editable) {

      jQuery('div.group_img', editable.obj).each(function () {
        // wrap image tag with required wrappers
        var $groupImg = jQuery(this);

        // create block
        $groupImg.alohaBlock({'aloha-block-type': 'ImageBlock'});
      });

      jQuery('img', editable.obj).each(function () {
        var $img = jQuery(this);

        if ($img.closest('div.group_img').length !== 0) {
          return
        }

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

    var startTemplating = function (img) {
      var editorWidth = jQuery('#contenteditor').width();
      var rightMarginBetweenImages = 6;

      var availableTemplates = [
        'image-layout-1image',
        'image-layout-1image_1caption_bottom',
        'image-layout-1image_1caption_left',
        'image-layout-1image_1caption_right',
        'image-layout-2images',
        'image-layout-2images_1caption_bottom',
        'image-layout-2images_2captions_bottom'
      ];

      jQuery('.bk-image-editor-start, .bk-image-layout-select', $popup).hide();
      jQuery('.bk-image-layout-selected, .bk-image-layout-ui-controls', $popup).show();

      $popup.css('top', parseInt($popup.css('top')) - 215);
      isImageUnderTemplating = true;

      var $img = jQuery(img);
      var $divImage = $img.closest('div.image');
      var $groupImg = $img.closest('div.group_img');
      var $nextDivImage = null;
      var $nextGroupImg = null;
      var renderedModalInfoPopup = null;
      var modalInfoPopup = null;
      var nextDivImage = null;
      var nextLayout = null;

      // get current layout
      var currentLayout = BkImageEditor.getImageLayout($divImage[0]);
      var initialLayout = currentLayout;

      // forbidden for FPI images
      if (JSON.parse($img.attr('transform-data')).frameFPI) {
        renderedModalInfoPopup = _.template(jQuery19('#modalInfoPopup').html())({
          "header": window.booktype._('layouting_not_possible', 'Layouting is not possible.'),
          "body": window.booktype._('layouting_not_possible_body', 'Layouting is not possible for full page images.')
        });
        modalInfoPopup = jQuery19(jQuery19.trim(renderedModalInfoPopup));
        modalInfoPopup.modal("show");
        stopTemplating($img);
        return;
      }

      // display layout as selected
      jQuery('.bk-image-layout-ui-controls img.' + currentLayout).addClass('selected');
      // add layout to groupImg
      $groupImg.addClass(currentLayout);

      jQuery('.bk-image-layout-ui-controls img').click(function () {
        var action = null;
        var $this = jQuery(this);

        $this.attr('class').split(' ').forEach(function (val) {
          if (val.indexOf('image-layout-') === 0) {
            action = val;
          }
        });

        if (currentLayout === action) return;

        // prepare captions
        var captionLeftBottomTEXT = 'Caption text';

        var captionSampleHTML =
          '<div class="caption_wrapper">' +
            '<div class="caption_small aloha-editable aloha-ephemera-attr" ' +
              'data-aloha-ephemera-attr="style" ' +
              'style="width: ' + $divImage.width() + 'px;" ' +
              'contenteditable="true" >' + captionLeftBottomTEXT +
            '</div>' +
          '</div>';

        /////////////////////////////
        /// RESTORE DEFAULT LAYOUT //
        /////////////////////////////

        // default layouts: image-layout-1image, image-layout-1image_1caption_bottom
        if (
          currentLayout === 'image-layout-1image_1caption_left' ||
          currentLayout === 'image-layout-1image_1caption_right'
        ) {
          // mark with default layout
          $groupImg.removeClass(currentLayout);
          $groupImg.addClass('image-layout-1image_1caption_bottom');
          currentLayout = 'image-layout-1image_1caption_bottom';
        }
        // 2 IMAGES //
        else if (currentLayout === 'image-layout-2images') {
          // restore default structure
          $nextDivImage = jQuery($groupImg.find('div.image')[1]).detach();
          $nextGroupImg = jQuery('<div/>', {class: 'group_img'});

          $groupImg.after($nextGroupImg);
          $nextGroupImg.append($nextDivImage);
          $nextGroupImg.alohaBlock({'aloha-block-type': 'ImageBlock'});

          $groupImg.removeClass(currentLayout);
          $groupImg.addClass('image-layout-1image_1caption_bottom');

          // mark with default layout
          $groupImg.removeClass(currentLayout);
          $groupImg.addClass('image-layout-1image');
          $nextGroupImg.addClass('image-layout-1image');

          currentLayout = 'image-layout-1image';
          nextLayout = 'image-layout-1image';
        }
        else if (currentLayout === 'image-layout-2images_1caption_bottom') {
          // restore default structure
          $nextDivImage = jQuery($groupImg.find('div.image')[1]).detach();
          $nextGroupImg = jQuery('<div/>', {class: 'group_img'});

          $groupImg.after($nextGroupImg);
          $nextGroupImg.append($nextDivImage);
          $nextGroupImg.alohaBlock({'aloha-block-type': 'ImageBlock'});

          // mark with default layout
          $groupImg.removeClass(currentLayout);
          $groupImg.addClass('image-layout-1image_1caption_bottom');
          $nextGroupImg.addClass('image-layout-1image');

          currentLayout = 'image-layout-1image_1caption_bottom';
          nextLayout = 'image-layout-1image';
        }
        else if (currentLayout === 'image-layout-2images_2captions_bottom') {
          // restore default structure

          // unwrapp 1st div
          jQuery($groupImg.find('div.wrap')[0]).find('div.image').unwrap();

          var $nextDivWrap = jQuery($groupImg.find('div.wrap')[0]).detach();
          $nextGroupImg = jQuery('<div/>', {class: 'group_img'});

          $groupImg.after($nextGroupImg);
          $nextGroupImg.append($nextDivWrap);
          $nextGroupImg.find('div.image').unwrap();
          $nextGroupImg.alohaBlock({'aloha-block-type': 'ImageBlock'});

          // mark with default layout
          $groupImg.removeClass(currentLayout);
          $groupImg.addClass('image-layout-1image_1caption_bottom');
          $nextGroupImg.addClass('image-layout-1image_1caption_bottom');

          currentLayout = 'image-layout-1image_1caption_bottom';
          nextLayout = 'image-layout-1image_1caption_bottom';
        }


        ///////////////
        /// ACTIONS ///
        ///////////////

        // 1 IMAGE NO CAPTION //
        if (action === 'image-layout-1image') {
          // just remove caption
          if (currentLayout === 'image-layout-1image_1caption_bottom') {
            $groupImg.find('.caption_wrapper').remove();
          }
        }
        // 1 IMAGE 1 CAPTION BOTTOM //
        else if (action === 'image-layout-1image_1caption_bottom') {
          if (currentLayout === 'image-layout-1image') {
            $groupImg.append(captionSampleHTML);
          }
        }
        // 1 IMAGE 1 CAPTION LEFT //
        else if (action === 'image-layout-1image_1caption_left') {
          // check if we have enough space for caption
          if ((editorWidth - $divImage.width()) < 50) {
            renderedModalInfoPopup = _.template(jQuery19('#modalInfoPopup').html())({
              "header": window.booktype._('layout_not_available', 'Layout is not available.'),
              "body": window.booktype._('layout_not_available_body',
                'There is no space to fit a caption. Make your image more narrow, using built in image editor.')
            });
            modalInfoPopup = jQuery19(jQuery19.trim(renderedModalInfoPopup));
            modalInfoPopup.modal("show");

            return;
          }

          if (currentLayout === 'image-layout-1image') {
            $groupImg.append(captionSampleHTML);
          }
        }
        // 1 IMAGE 1 CAPTION RIGHT //
        else if (action === 'image-layout-1image_1caption_right') {
          // check if we have enough space for caption
          if ((editorWidth - $divImage.width()) < 50) {
            renderedModalInfoPopup = _.template(jQuery19('#modalInfoPopup').html())({
              "header": window.booktype._('layout_not_available', 'Layout is not available.'),
              "body": window.booktype._('layout_not_available_body',
                'There is no space to fit a caption. Make your image more narrow, using built in image editor.')
            });
            modalInfoPopup = jQuery19(jQuery19.trim(renderedModalInfoPopup));
            modalInfoPopup.modal("show");

            return;
          }

          if (currentLayout === 'image-layout-1image') {
            $groupImg.append(captionSampleHTML);
          }
        }
        // 2 IMAGES //
        else if (action === 'image-layout-2images') {
          // validate next structure
          $nextGroupImg = $groupImg.next();
          if (
            !$nextGroupImg.length ||
            !$nextGroupImg.hasClass('group_img') ||
            !$nextGroupImg.find('.image').length ||
            !$nextGroupImg.find('.image').hasClass('image')
          ) {
            renderedModalInfoPopup = _.template(jQuery19('#modalInfoPopup').html())({
              "header": window.booktype._('layout_not_available', 'Layout is not available.'),
              "body": window.booktype._('layout_not_available_body',
                'Image below is required. To combine 2 images, please, insert second image right after current one.')
            });
            modalInfoPopup = jQuery19(jQuery19.trim(renderedModalInfoPopup));
            modalInfoPopup.modal("show");

            return
          }
          nextDivImage = $nextGroupImg.find('.image');
          nextLayout = BkImageEditor.getImageLayout(nextDivImage);

          // just remove caption
          if (currentLayout === 'image-layout-1image_1caption_bottom') {
            $groupImg.find('.caption_wrapper').remove();
          }
          // append second image
          $groupImg.append(nextDivImage);
          // let's fit 2 images
          if ($divImage.width() > (editorWidth - rightMarginBetweenImages) / 2) {
            BkImageEditor.proportionalResize(
              img,
              $divImage[0],
              (editorWidth - rightMarginBetweenImages) / 2,
              editorWidth
            );
          }
          if (nextDivImage.width() > (editorWidth - rightMarginBetweenImages) / 2) {
            BkImageEditor.proportionalResize(
              nextDivImage.find('img')[0],
              nextDivImage[0],
              (editorWidth - rightMarginBetweenImages) / 2,
              editorWidth
            );
          }
          // remove 2nd image block
          $nextGroupImg.remove();
        }
        // 2 IMAGES 1 CAPTION BOTTOM //
        else if (action === 'image-layout-2images_1caption_bottom') {
          // validate next structure
          $nextGroupImg = $groupImg.next();
          if (
            !$nextGroupImg.length ||
            !$nextGroupImg.hasClass('group_img') ||
            !$nextGroupImg.find('.image').length ||
            !$nextGroupImg.find('.image').hasClass('image')
          ) {
            renderedModalInfoPopup = _.template(jQuery19('#modalInfoPopup').html())({
              "header": window.booktype._('layout_not_available', 'Layout is not available.'),
              "body": window.booktype._('layout_not_available_body',
                'Image below is required. To combine 2 images, please, insert second image right after current one.')
            });
            modalInfoPopup = jQuery19(jQuery19.trim(renderedModalInfoPopup));
            modalInfoPopup.modal("show");

            return
          }
          nextDivImage = $nextGroupImg.find('.image');
          nextLayout = BkImageEditor.getImageLayout(nextDivImage);

          // add caption to the first image if it does not exist
          if (currentLayout === 'image-layout-1image') {
            $groupImg.append(captionSampleHTML);
          }
          // append second image
          $divImage.after(nextDivImage);
          // let's fit 2 images
          if ($divImage.width() > (editorWidth - rightMarginBetweenImages) / 2) {
            BkImageEditor.proportionalResize(
              img,
              $divImage[0],
              (editorWidth - rightMarginBetweenImages) / 2,
              editorWidth
            );
          }
          if (nextDivImage.width() > (editorWidth - rightMarginBetweenImages) / 2) {
            BkImageEditor.proportionalResize(
              nextDivImage.find('img')[0],
              nextDivImage[0],
              (editorWidth - rightMarginBetweenImages) / 2,
              editorWidth
            );
          }
          // remove 2nd image block
          $nextGroupImg.remove();

        }
        // 2 IMAGES 2 CAPTIONS BOTTOM //
        else if (action === 'image-layout-2images_2captions_bottom') {
          // validate next structure
          $nextGroupImg = $groupImg.next();
          if (
            !$nextGroupImg.length ||
            !$nextGroupImg.hasClass('group_img') ||
            !$nextGroupImg.find('.image').length ||
            !$nextGroupImg.find('.image').hasClass('image')
          ) {
            renderedModalInfoPopup = _.template(jQuery19('#modalInfoPopup').html())({
              "header": window.booktype._('layout_not_available', 'Layout is not available.'),
              "body": window.booktype._('layout_not_available_body',
                'Image below is required. To combine 2 images, please, insert second image right after current one.')
            });
            modalInfoPopup = jQuery19(jQuery19.trim(renderedModalInfoPopup));
            modalInfoPopup.modal("show");

            return
          }
          nextDivImage = $nextGroupImg.find('.image');
          nextLayout = BkImageEditor.getImageLayout(nextDivImage);

          // add caption to the first image if it does not exist
          if (currentLayout === 'image-layout-1image') {
            $groupImg.append(captionSampleHTML);
          }
          // add caption to the second image if it does not exist
          if (nextLayout === 'image-layout-1image') {
            $nextGroupImg.append(captionSampleHTML);
          }

          // wrap image and caption with extra div
          var $firstWrap = jQuery('<div/>', {class: 'wrap'});
          var $secondWrap = jQuery('<div/>', {class: 'wrap'});

          $groupImg.contents().wrapAll($firstWrap);
          $nextGroupImg.contents().wrapAll($secondWrap);

          // combine images (wraps)
          $groupImg.find('.wrap').after($nextGroupImg.find('.wrap'));

          // let's fit 2 images
          if ($divImage.width() > (editorWidth - rightMarginBetweenImages) / 2) {
            BkImageEditor.proportionalResize(
              img,
              $divImage[0],
              (editorWidth - rightMarginBetweenImages) / 2,
              editorWidth
            );
          }
          if (nextDivImage.width() > (editorWidth - rightMarginBetweenImages) / 2) {
            BkImageEditor.proportionalResize(
              nextDivImage.find('img')[0],
              nextDivImage[0],
              (editorWidth - rightMarginBetweenImages) / 2,
              editorWidth
            );
          }
          // sync captions width
          $groupImg.find('div.caption_small:first').width($divImage.width());
          $groupImg.find('div.caption_small:last').width(nextDivImage.width());

          // remove 2nd image block
          $nextGroupImg.remove();

        }

        // change layout UI
        var imgs = jQuery('.bk-image-layout-ui-controls img');
        imgs.removeClass('selected');
        $this.addClass('selected');
        // change layout groupImg
        $groupImg.removeClass(currentLayout);
        $groupImg.addClass(action);
        currentLayout = action;

        BkImageEditor.scaleImages(
          Aloha.getEditableById('contenteditor').obj,
          editorWidth
        );

      });
    };

    var stopTemplating = function (img) {
      jQuery('.bk-image-editor-start, .bk-image-layout-select', $popup).show();
      jQuery('.bk-image-layout-selected, .bk-image-layout-ui-controls', $popup).hide();
      $popup.css('top', parseInt($popup.css('top')) + 215);

      isImageUnderTemplating = false;

      var imgs = jQuery('.bk-image-layout-ui-controls img');
      imgs.removeClass('selected');
      imgs.unbind('click');
    };

    var startEdit = function (img) {
      if (isImageUnderTemplating) stopTemplating(img);

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
      jQuery('.bk-image-editor-start, .bk-image-layout-select', $popup).hide();
      $popup.css('top', parseInt($popup.css('top')) - 255);
      isImageUnderEdit = true;
    };

    var stopEdit = function () {
      PubSub.pub('bk-image-editor.stop', {});

      jQuery('.bk-image-editor-stop, .bk-image-editor-ui-controls', $popup).hide();
      jQuery('.bk-image-editor-start, .bk-image-layout-select', $popup).show();
      jQuery('.bk-image-layout-selected', $popup).hide();
      $popup.css('top', parseInt($popup.css('top')) + 255);
      isImageUnderEdit = false;
    };

    return Plugin.create('imagesimple', {
      makeClean: function (obj) {

        jQuery(obj).find('DIV.group_img').each(function () {
          var imageLayout = null;
          var $groupImg = jQuery(this);

          // find image layout
          $groupImg.attr('class').split(' ').forEach(function (val) {
            if (val.indexOf('image-layout-') === 0) {
              imageLayout = val;
            }
          });

          // create new group_img
          var $newGroupImg = jQuery('<div class="group_img"></div>');
          $newGroupImg.css('text-align', $groupImg.css('text-align'));

          // append div.image or div.wrap
          if (imageLayout === 'image-layout-2images_2captions_bottom') {
            $newGroupImg.append($groupImg.find('div.wrap'));
          } else {
            $newGroupImg.append($groupImg.find('div.image'));
          }

          // add image layout
          if (imageLayout) {
            $newGroupImg.addClass(imageLayout);
          }

          if (imageLayout === 'image-layout-2images_2captions_bottom') {
            $newGroupImg.find('div.caption_small').unwrap();
            $newGroupImg.find('div.caption_small').attr('class', 'caption_small');
            $newGroupImg.find('div.caption_small').removeAttr('id')
          } else {
            // find caption if it exists
            var $divCaptionSmall = $groupImg.find('div.caption_small');
            if ($divCaptionSmall.length > 0) {
              $divCaptionSmall.attr('class', 'caption_small');
              $divCaptionSmall.removeAttr('id');
              $divCaptionSmall.removeAttr('data-aloha-ephemera-attr');
              $divCaptionSmall.removeAttr('contenteditable');
              $newGroupImg.append($divCaptionSmall);
            }
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

        // add search input handler
        var searchInput = jQuery19('#media-image-search input');
        searchInput.keyup(function () {
          var searchText = jQuery19(this).val().trim();

          jQuery19('.uploads-grid img').each(function (k, v) {
            var img = jQuery19(v);
            var li = img.parent();
            var keywords = img.attr('data-search').split(',');

            for (var i = 0; i < keywords.length; i++) {
              if (keywords[i].indexOf(searchText) !== -1) {
                li.show();
                break;
              } else {
                li.hide();
              }
            }
          })
        });

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

          jQuery19('#renameMedia .btn-primary').bind('click.simpleimage', function () {
            var mediaID = jQuery19('#renameMedia INPUT[name=attachment]').attr('value').split(',');
            var filename = jQuery19('#renameMedia INPUT[name=filename]').attr('value').trim();

            var $alert = jQuery19('#renameMedia div.alert');
            $alert.addClass('hide');

            if (mediaID.length === 0 || filename === '') {
              return;
            }

            booktype.ui.notify(booktype._('rename_media_file', 'Rename media file'));

            booktype.sendToCurrentBook({
                'command': 'attachment_rename',
                'attachments': mediaID,
                'filename': filename,
              },
              function (data) {

                if (!data.result) {
                  if (data.message) {
                    $alert.html(data.message).removeClass('hide');
                  }
                  return
                }

                booktype.ui.notify();
                jQuery19('#renameMedia').modal('hide');
                reloadAttachments();

                jQuery19('#medialibrary').removeClass('open-info');

                // Trigger event
                jQuery19(document).trigger('booktype-attachment-renamed');
              });

          });

        });

        // ImagePopup remove
        jQuery19('a.remove', $popup).on('click', function ($e) {
          // Is this image in a div ?

          if ($imageInFocus.closest('.group_img').length) {
            $imageInFocus.closest('div.group_img').remove();
          } else {
            $imageInFocus.remove();
          }

          $e.stopPropagation();
          $e.preventDefault();
          $popup.hide();

          stopEdit();
          stopTemplating();

          doNothing = true;

          // This is so stupid
          setTimeout(function () {
            doNothing = false;
          }, 100);

          // publish message notification that image was deleted
          PubSub.pub('toolbar.action.triggered', {'event': $e});
          return false;
        });

        // ImagePopup start templating
        jQuery19('a.bk-image-layouts-list', $popup).on('click', function ($e) {
          var $img = $imageInFocus.closest('div.group_img').find('div.image:first').find('img');
          startTemplating($img[0]);
          return false;
        });

        // ImagePopup stop templating
        jQuery19('a.bk-image-layout-selected', $popup).on('click', function ($e) {
          stopTemplating($imageInFocus[0]);
          return false;
        });

        // ImagePopup start edit
        jQuery19('a.bk-image-editor-start', $popup).on('click', function ($e) {
          startEdit($imageInFocus[0]);

          var layout = BkImageEditor.getImageLayout($imageInFocus.closest('div.image'));

          if (layout !== 'image-layout-1image' && layout !== 'image-layout-1image_1caption_bottom') {
            jQuery19('input[bk-image-editor-action="toggle_fpi"]').parent().hide();
          } else {
            jQuery19('input[bk-image-editor-action="toggle_fpi"]').parent().show();
          }

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
          isImageUnderEdit = isImageUnderTemplating = false;
          $popup.hide();
        });

        Aloha.bind('aloha-selection-changed', function (event, rangeObject, originalEvent) {
          if (doNothing) {
            return;
          }

          if (!isImageUnderEdit && !isImageUnderTemplating) {
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
