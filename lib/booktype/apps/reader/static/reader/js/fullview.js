(function (win, $) {
  'use strict';
  
  $(function () {

    var bookcontent = $('#bookcontent');

    $('div.group_img', bookcontent).each(function () {
      var $div_caption_wrapper = null;
      var div_group_img = $(this);
      var $div_caption_small = div_group_img.find('div.caption_small');

      if ($div_caption_small.length === 0) {
        var $p_caption_small = div_group_img.find('p.caption_small');

        // convert old formated caption_small to new format using div
        if ($p_caption_small.length && $p_caption_small.html().length) {
          $div_caption_small = $('<div class="caption_small">' + $p_caption_small.html() + '</div>');
          $div_caption_wrapper = $('<div class="caption_wrapper">' + $div_caption_small.prop('outerHTML') + '</div>');
          $p_caption_small.replaceWith($div_caption_wrapper);
        }

      } else {
        // convert new style caption_small with div
        $div_caption_wrapper = $('<div class="caption_wrapper">' + $div_caption_small.prop('outerHTML') + '</div>');
        $div_caption_small.replaceWith($div_caption_wrapper);
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