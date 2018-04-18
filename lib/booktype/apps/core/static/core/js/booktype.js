(function (win, $) {
  'use strict';

  $(function () {
    // globally enable some bootstrap plugins
    $('[rel=tooltip]').tooltip({
      container: 'body',
      trigger: 'hover'
    });

    // btn group that activate buttons in a mutually exclusive way
    $(document).on('click', '[data-toggle="btns"] .btn', function () {
    	var $this = $(this);
    	$this.parent().find('.active').removeClass('active');
      $this.addClass('active');
    });

    // inside try for now.
    // @TODO: I'll organize assets later
    try {
      // enable alerts
      $('.alert').alert();
    } catch (e) {}


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

    // Loading modal's content from a remote address was deprecated in bootstrap 3.3
    // so, we need to trick this out a bit to keep working with the current
    // logic which was just fine.
    $(document).on('click', '[data-toggle=modal][data-remote]', function (){
      var target = $(this).data('target');
      var url = $(this).data('remote');

      $(target)
        .load(url)
        .modal('show');
    });
  });
})(window, jQuery);
