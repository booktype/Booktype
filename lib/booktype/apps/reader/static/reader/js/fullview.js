(function (win, $) {
  'use strict';
  
  $(function () {
    // enable kind of softly scroll
    $('.chapter_link').click(function () {
      $('html, body').animate({
        scrollTop: $($.attr(this, 'href')).offset().top - 120
      }, 1000);
      return false;
    });
  });

})(window, jQuery);