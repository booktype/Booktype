(function (win, $) {
  'use strict';
  
  $(function () {

    var bookcontent = $('#bookcontent');

    $('div.group_img', bookcontent).each(function () {
      var $divCaptionWrapper = null;
      var $divGroupImg = $(this);
      var $divCaptionSmall = $divGroupImg.find('div.caption_small');

      if ($divCaptionSmall.length === 0) {
        var $pCaptionSmall = $divGroupImg.find('p.caption_small');

        // convert old formated caption_small to new format using div
        if ($pCaptionSmall.length && $pCaptionSmall.html().length) {
          $divCaptionSmall = $('<div class="caption_small">' + $pCaptionSmall.html() + '</div>');
          $divCaptionWrapper = $('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
          $pCaptionSmall.replaceWith($divCaptionWrapper);
        }

      } else {
        // convert new style caption_small with div
        $divCaptionWrapper = $('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
        $divCaptionSmall.replaceWith($divCaptionWrapper);
      }
    });


    BkImageEditorScaleImages(bookcontent, bookcontent.width());

    $(window).resize(function () {
      BkImageEditorScaleImages(bookcontent, bookcontent.width());
    });

    $('#bookcontent p a[href^="../"]').each(function () {
      var $a = $(this);
      var chapterSlug = $a.attr('href').split('/')[1];

      if ($('a.chapter_link[href="#' + chapterSlug +'"]').length) {
        $a.addClass('chapter_link');
        $a.attr('href', '#' + chapterSlug);
      } else {
        $a.removeAttr('href');
      }
    });

    // enable kind of softly scroll
    $('.chapter_link').click(function () {
      $('html, body').animate({
        scrollTop: $($.attr(this, 'href')).offset().top - 120
      }, 1000);
      return false;
    });
  });

})(window, jQuery);