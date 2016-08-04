(function (win, jQuery) {
  'use strict';

  jQuery(function () {

    var bookcontent = jQuery('#bookcontent');

    jQuery('div.group_img', bookcontent).each(function () {
        var $div_caption_wrapper = null;
        var div_group_img = jQuery(this);
        var $div_caption_small = div_group_img.find('div.caption_small');

        if ($div_caption_small.length === 0) {
          var $p_caption_small = div_group_img.find('p.caption_small');

          // convert old formated caption_small to new format using div
          if ($p_caption_small.length && $p_caption_small.html().length) {
            $div_caption_small = jQuery('<div class="caption_small">' + $p_caption_small.html() + '</div>');
            $div_caption_wrapper = jQuery('<div class="caption_wrapper">' + $div_caption_small.prop('outerHTML') + '</div>');
            $p_caption_small.replaceWith($div_caption_wrapper);
          }

        } else {
          // convert new style caption_small with div
          $div_caption_wrapper = jQuery('<div class="caption_wrapper">' + $div_caption_small.prop('outerHTML') + '</div>');
          $div_caption_small.replaceWith($div_caption_wrapper);
        }
    });

    BkImageEditorScaleImages(bookcontent, bookcontent.width());

    jQuery(window).resize(function () {
      BkImageEditorScaleImages(bookcontent, bookcontent.width());
    });

  });

})(window, jQuery);