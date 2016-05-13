(function (win, jQuery) {
  'use strict';

  jQuery(function () {

    var bookcontent = jQuery('#bookcontent');

    BkImageEditorScaleImages(bookcontent, bookcontent.width());

    jQuery(window).resize(function () {
      BkImageEditorScaleImages(bookcontent, bookcontent.width());
    });

  });

})(window, jQuery);