(function (win, $) {
  'use strict';
  
  $(function () {
    // globally enable some bootstrap plugins
    $('[rel=tooltip]').tooltip({
      container: 'body'
    });

    // enable alerts
    $('.alert').alert();

    // fade out all alerts with bk-dismiss class. 
    // time to dismiss needs to be set up as data-attribute
    // e.g: data-dismiss-secs="10" for 10 seconds
    $('.bk-dismiss').each(function (i, alert) {
      var timeout = $(alert).data('dismiss-secs');
      setTimeout(function () {
        $(alert).fadeOut(1000, 'linear');
      }, parseInt(timeout, 10) * 1000);
    });

    // use button tag as link with trigger url attribute
    $(document).on('click', 'button[data-href]', function () {
      win.location.href = $(this).data('href');
    });
    $('.collapse-navigation a').click(function () {
      $('body').toggleClass('menu-open');
    });

    // We need this in case we are using same modal container
    // and just replacing the content
    $(document).on('hidden.bs.modal', '.cleanModalInfo', function () {
      $(this).removeData('bs.modal').html('');
    });
  });
})(window, jQuery);