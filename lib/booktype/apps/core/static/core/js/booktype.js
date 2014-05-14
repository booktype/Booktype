(function (win, $) {
  'use strict';
  
  $(function () {
    // globally enable tooltips
    $('[rel=tooltip]').tooltip({
      container: 'body'
    });

    // use button tag as link with trigger url attribute
    $(document).on('click', 'button[data-href]', function () {
      win.location.href = $(this).data('href');
    });
  });
})(window, jQuery);