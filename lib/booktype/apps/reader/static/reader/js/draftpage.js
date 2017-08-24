(function (win, jQuery) {
  'use strict';

  jQuery(function () {

    var bookcontent = jQuery('#bookcontent');

    jQuery('div.group_img', bookcontent).each(function () {
        var $divCaptionWrapper = null;
        var $divGroupImg = jQuery(this);
        var $divCaptionSmall = $divGroupImg.find('div.caption_small');

        if ($divCaptionSmall.length === 0) {
          var $pCaptionSmall = $divGroupImg.find('p.caption_small');

          // convert old formated caption_small to new format using div
          if ($pCaptionSmall.length && $pCaptionSmall.html().length) {
            $divCaptionSmall = jQuery('<div class="caption_small">' + $pCaptionSmall.html() + '</div>');
            $divCaptionWrapper = jQuery('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
            $pCaptionSmall.replaceWith($divCaptionWrapper);
          }

        } else {
          // convert new style caption_small with div
          $divCaptionWrapper = jQuery('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
          $divCaptionSmall.replaceWith($divCaptionWrapper);
        }
    });

    win.booktype.utils.bkImageEditorScaleImages(bookcontent, bookcontent.width());

    jQuery(window).resize(function () {
      win.booktype.utils.bkImageEditorScaleImages(bookcontent, bookcontent.width());
    });

  });

})(window, jQuery);
