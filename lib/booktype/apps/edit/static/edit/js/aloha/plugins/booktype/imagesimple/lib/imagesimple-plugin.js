define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'booktype', 'underscore', 'PubSub', 'image/image-plugin'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Console, Ephemera, block, BlockManager, booktype, _, PubSub, image) {
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

    // Define Image Block
    var ImageBlock = block.AbstractBlock.extend({
      title: 'Image',
      isDraggable: function () {
        return false;
      },
      init: function ($element, postProcessFn) {
        var $desc = $element.find('p');
        var $n = jQuery('<div class="caption_small center aloha-editable">' + $desc.html() + '</div>');

        $desc.replaceWith($n);

        return postProcessFn();
      },
      update: function ($element, postProcessFn) {
        return postProcessFn();
      }
    });

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

    };

    var reloadAttachments = function (callback) {
      booktype.sendToCurrentBook({'command': 'attachments_list'},
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
      var $t = _.template(jQuery19('#templateImageThumbnail').html());

      jQuery19('.uploads-grid', $manager).empty();

      _.each(attachments, function (att, i) {
        var $i = $t({'name': att.name, 'media_id': att.id});
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
        var imgsrc = jQuery19(this).find('img').attr('src');
        jQuery19('.image-preview img', $manager).attr('src', imgsrc);

        var imgHeight = jQuery19('.image-preview img', $manager).height();
        var imgMargin = Math.round((226 - imgHeight) / 2) + 'px';

        jQuery19('.image-preview img', $manager).css('margin-top', imgMargin);

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
        var $div_image = $img.closest('div.image');
        var group_img = $img.closest('div.group_img');

        if ($div_image.length === 0) {
          $img.wrap(jQuery('<div/>', {class: 'image'}));
        }

        if (group_img.length === 0) {
          $img.parent().wrap(jQuery('<div/>', {class: 'group_img'}));
        }

        group_img = $img.closest('div.group_img');

        group_img.find('div.image:first').attr('contenteditable', false);
        group_img.find('div.image:first').css('text-align', 'left');

        // create block
        group_img.alohaBlock({'aloha-block-type': 'ImageBlock'});
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
      $popup.css('top', parseInt($popup.css('top')) - 85);
      isImageUnderEdit = true;
    };

    var stopEdit = function () {
      PubSub.pub('bk-image-editor.stop', {});

      jQuery('.bk-image-editor-stop, .bk-image-editor-ui-controls', $popup).hide();
      jQuery('.bk-image-editor-start', $popup).show();
      $popup.css('top', parseInt($popup.css('top')) + 85);
      isImageUnderEdit = false;
    };

    return Plugin.create('imagesimple', {
      makeClean: function (obj) {
        jQuery(obj).find('DIV.group_img').each(function () {
          var $div = jQuery(this);
          var $d = jQuery('<div class="group_img"></div>');

          $d.append($div.find('div.image'));

          var $desc = $div.find('div.caption_small');

          if ($desc.length > 0) {
            var $d0 = jQuery('<p class="caption_small center">' + $desc.html() + '</p>');
            $d.append($d0);
          }
          $div.replaceWith($d);
        });

        jQuery(obj).find('.image-focus').each(function () {
          var $div = jQuery(this);
          $div.removeClass('image-focus');
        });

      },

      init: function () {
        $manager = jQuery19(document).find('#imageManager');
        $popup = jQuery19('#imagePopup');

        BlockManager.registerBlockType('ImageBlock', ImageBlock);
        var alertWrapper = jQuery19('.alert-wrapper');

        jQuery19('.upload-file', $manager).fileupload({
          dataType: 'json',
          sequentialUploads: true,
          done: function (e, data) {
            reloadAttachments(function () {
              jQuery19('a.medialibrary', $manager).tab('show');
            });

            jQuery19('.upload-file', $manager).prop('disabled', false);
            jQuery19(document).trigger('booktype-attachment-uploaded', [data.files]);

            alertWrapper.addClass('hidden');
          },
          add: function (e, data) {
            jQuery19('.upload-file', $manager).prop('disabled', true);
            alertWrapper.removeClass('hidden');
            data.formData = [{'name': 'clientID', 'value': window.booktype.clientID}];
            fileUpload = data.submit();
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

          var $d = jQuery('<div class="group_img"></div>');
          var $d2 = jQuery('<div class="image"></div>');
          $d2.append($image);
          $d.append($d2);

          if (description !== '') {
            $d.append(jQuery('<p class="caption_small center">' + description + '</p>'));
          }

          $d.alohaBlock({'aloha-block-type': 'ImageBlock'});

          // Sometimes IE has issues with focus. In case when IE looses focus, this should
          // probably to the work
          var $editable = Aloha.getEditableById('contenteditor');
          GENTICS.Utils.Dom.insertIntoDOM($d, range, $editable.obj);

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
              $popup.css('top', y - 85 - 40);
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
                $popup.css('top', y - 85 - 40);
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
                $popup.css('top', y - 85 - 40);
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
