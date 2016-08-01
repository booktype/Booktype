var getAvatar = function (username, size) {
  // MD5 (Message-Digest Algorithm) by WebToolkit
  // http://www.webtoolkit.info/javascript-md5.html
  var size = size || 80;
  return '/_utils/profilethumb/' + username + '/thumbnail.jpg?width=' + size
};


function validateEmail(email) {
  var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(email);
}


function BkImageEditorScaleImages($container, toWidth) {
  // because it's wrong
  if (toWidth <= 0) return;

  // walked through all images
  jQuery('div.group_img div.image', $container).each(function () {
    var $frame = jQuery(this);
    var $image = jQuery(this).find('img');
    var $caption = $frame.parent().find('p.caption_small');
    var transformData = $image.attr('transform-data');

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

      // apply new css width for image caption if it exists
      if ($caption.length) {
        $caption.width(scaledFrameWidth);
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
}
