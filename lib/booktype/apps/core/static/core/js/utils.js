(function (win, jquery, _) {
  'use strict';

  jquery.namespace('win.booktype.utils');

  /*
    Utility functions.
    TODO: put here the rest of utils from booki.js file
   */
  var bkUtils = (function () {
    return {
      validateEmail: function (email) {
        var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(email);
      },

      /**
       * Returns a user thumbnail url for the given size
       *
       * @param {string} username who is the avatar required
       * @param {string} size desired thumbnail size
       */
      getAvatar: function (username, size) {
        // MD5 (Message-Digest Algorithm) by WebToolkit
        // http://www.webtoolkit.info/javascript-md5.html
        var size = size || 80;
        return '/_utils/profilethumb/' + username + '/thumbnail.jpg?width=' + size
      },

      bkImageEditorScaleImages: function ($container, toWidth) {
        function getImageLayout(frame) {
          var $frame = jQuery(frame);
          var layout = null;

          $frame.closest('.group_img').attr('class').split(' ').forEach(function (val) {
            if (val.indexOf('image-layout-') === 0) {
              layout = val;
            }
          });

          if (!layout) {
            if ($frame.next().hasClass('caption_wrapper')) {
              layout = 'image-layout-1image_1caption_bottom'
            } else {
              layout = 'image-layout-1image'
            }
          }

          return layout;
        }

        // because it's wrong
        if (toWidth <= 0) return;

        // walked through all images
        jquery('div.group_img div.image', $container).each(function () {
          var $frame = jquery(this);
          var $image = jquery(this).find('img');
          var $caption = $frame.parent().find('.caption_small');
          var transformData = $image.attr('transform-data');

          // get current image template
          var currentLayout = getImageLayout($frame);

          // sync caption width with frame
          if (currentLayout === 'image-layout-1image_1caption_bottom') {
            if ($caption.length) {
              $caption.width($frame.width());
            }
          }
          else if (
            currentLayout === 'image-layout-1image_1caption_left' ||
            currentLayout === 'image-layout-1image_1caption_right'
          ) {
            if ($caption.length) {
              $caption.width(
                toWidth - parseInt($frame.width()) - 20
              );
            }
          }
          else if (
            currentLayout === 'image-layout-2images_1caption_bottom' &&
            $frame.next().hasClass('caption_wrapper')
          ) {
            $caption.width(
              $frame.prev().width() + $frame.width()
            );
          }

          // if image was not edited
          if (!_.isUndefined(transformData)) {
            transformData = JSON.parse(transformData);
            var quotient = transformData['editorWidth'] / toWidth;

            // there is no changes
            if (quotient === 1) return;

            //////////////////////////////
            // make proportional resize //
            //////////////////////////////


            // current frame/image sizes defined in css
            var frameWidth = parseFloat($frame[0].style['width']);
            var frameHeight = parseFloat($frame[0].style['height']);
            var imageWidth = parseFloat($image[0].style['width']);
            var imageHeight = parseFloat($image[0].style['height']);

            if (!frameWidth) frameWidth = parseFloat($frame.width());
            if (!frameHeight) frameHeight = parseFloat($frame.height());
            if (!imageWidth) imageWidth = parseFloat($image.width());
            if (!imageHeight) imageHeight = parseFloat($image.height());

            if (frameWidth == 0 || frameHeight == 0 || imageWidth == 0 || imageHeight == 0) return;

            var scaledFrameWidth = frameWidth / quotient;
            var scaledFrameHeight = frameHeight / quotient;
            var scaledImageWidth = imageWidth / quotient;
            var scaledImageHeight = imageHeight / quotient;

            // apply new css width/height to image and frame
            $frame.css('width', scaledFrameWidth);
            $frame.css('height', scaledFrameHeight);
            $image.css('width', scaledImageWidth);
            $image.css('height', scaledImageHeight);

            // // apply new css width for image caption if it exists
            if (currentLayout === 'image-layout-1image_1caption_bottom') {
              if ($caption.length) {
                $caption.width(scaledFrameWidth);
              }
            }
            else if (
              currentLayout === 'image-layout-1image_1caption_left' ||
              currentLayout === 'image-layout-1image_1caption_right'
            ) {
              if ($caption.length) {
                $caption.width(
                  toWidth - parseInt(scaledFrameWidth) - 20
                );
              }
            }
            else if (
              currentLayout === 'image-layout-2images_1caption_bottom' &&
              $frame.next().hasClass('caption_wrapper')
            ) {
              $caption.width(
                $frame.prev().width() + scaledFrameWidth
              );
            }
            else if (
              currentLayout === 'image-layout-2images_2captions_bottom'
            ) {
              $caption.width(
                $frame.prev().width() + scaledFrameWidth
              );
            }

            // image transform css
            var transformCss = $image[0].style[Modernizr.prefixed('transform')];
            var imageTranslateX = 0;
            var imageTranslateY = 0;

            if (transformCss.search(/translate\(/i) !== -1) {
              var _translate = transformCss.split('translate(')[1].split(')')[0].split(',');

              imageTranslateX = parseFloat(_translate[0]);
              imageTranslateY = parseFloat(_translate[1]);
            }

            var imageScaledTranslateX = imageTranslateX / quotient;
            var imageScaledTranslateY = imageTranslateY / quotient;

            // apply new translate css to image
            $image[0].style[Modernizr.prefixed('transform')] = transformCss.replace(
              'translate(' + imageTranslateX + 'px, ' + imageTranslateY + 'px)',
              'translate(' + imageScaledTranslateX + 'px, ' + imageScaledTranslateY + 'px)'
            );

            // update transform-data
            transformData['editorWidth'] = toWidth;
            transformData['imageWidth'] = scaledImageWidth;
            transformData['imageHeight'] = scaledImageHeight;
            transformData['imageTranslateX'] = imageScaledTranslateX;
            transformData['imageTranslateY'] = imageScaledTranslateY;
            transformData['frameWidth'] = scaledFrameWidth;
            transformData['frameHeight'] = scaledFrameHeight;

            // record updated transform-data
            $image.attr('transform-data', JSON.stringify(transformData));
          }
        });
      },

      /**
       * Method to configure bootstrap datepicker
       * @param {string} - selector: DOM element selector to be the picker applied
       */
      initBsDatepicker: function (selector, params) {
        var selector = (typeof selector !== 'undefined') ? selector : '.bs-datepicker';
        var options = {
          autoclose: true,
          zIndexOffset: 1000,
          todayHighlight: true
        };

        // overwrite with custom settings
        jquery.extend(true, options, (params || {}));

        jquery(selector).datepicker(options);
      },

      /**
       * Method to download a given string as the provided content type
       * @param {string} - content: String to be downloaded as file content
       * @param {string} - filename
       * @param {string} - contentType: Desided content type to be used in download
       */
      download: function (content, filename, contentType) {
        if (!contentType) contentType = 'application/octet-stream';

        var a = document.createElement('a');
        var blob = new Blob([content], {'type': contentType});

        a.href = win.URL.createObjectURL(blob);
        a.download = filename;
        a.click();
      }

    };
  })();

  jquery.extend(true, win.booktype.utils, bkUtils)

})(window, jQuery, _);
