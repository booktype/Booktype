(function (win, $) {
  "use strict"

  win.booktype.utils.initBsDatepicker('.bs-datepicker', {
    startDate: "today"
  });

  // let's remove the previous clipboard to avoid double binds
  try {
    win.codeClipboard.destroy()
  } catch (e) {}

  // init clipboard copier
  var codeClipboard = new Clipboard('.btn-copy');

  codeClipboard.on('success', function(e) {
    console.info('Action:', e.action);
    console.info('Text:', e.text);
    // console.info('Trigger:', e.trigger);

    $(e.trigger).attr('data-title', $(e.trigger).data('success-title'));
    $(e.trigger).tooltip('show');
  });

  codeClipboard.on('error', function(e) {
    console.error('Action:', e.action);
    console.error('Trigger:', e.trigger);

    $(e.trigger).attr('data-title', $(e.trigger).data('error-title'));
    $(e.trigger).tooltip('show');
  });

  win.codeClipboard = codeClipboard;

  // init tooltips for modal
  $('[data-toggle="tooltip"]').tooltip();

  // handle loading text button
  $('.btn[data-loading-text]').on('click', function() {
    var $this = $(this);
    $this.button('loading');
  });

  // TODO: we should integrate a validation plugin or something like that
  $('#submitInviteForm').on('click', function (){
    var btn = $(this);
    var form = $(this).closest('form');
    var url = form.attr('action');
    var params = form.serialize();
    var errorsContainer = $('.form-errors');

    // let's hide the errors
    errorsContainer.addClass('hide');

    $.post(url, params, function (response) {
      if (response.result) {
        form.find('input').attr('disabled', true);
        form.find('#submitInviteForm').addClass('hide');
        form.find('.btn-done').removeClass('hide');

        $('#newCode')
          .text(response.code)
          .parent().removeClass('hide');
      } else {
        errorsContainer.find('ul li').remove();

        $.each(response.errors, function (id, err) {
          var label = $('label[for=id_' + id + ']').text();
          var li = $('<li>').html('<b>' + label.trim() + ':</b> ' + err[0]);
          li.appendTo(errorsContainer.find('ul'));
        });

        errorsContainer.removeClass('hide');
      }

      setTimeout(function (){
        btn.button('reset');
      }, 500);
    });
  });

})(window, jQuery);
