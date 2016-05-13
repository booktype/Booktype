(function (win, $) {
  'use strict';
  
  $(function () {

    var bookcontent = $('#bookcontent');

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