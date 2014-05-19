(function (win, $) {
  'use strict';
  
  $(function () {
    // related to Book Info Page
    $(document).on('hidden.bs.modal', '.bookInfoModal', function () {
      $(this).removeData('bs.modal').html('');
    });

    // Delete Book
    $(document).on('keyup paste', '.bookInfoModal input[name="title"]', function () {
      if ($(this).val() === $(this).attr('placeholder')) {
        $('.bookInfoModal .delete-book').removeAttr('disabled');
      } else {
        $('.bookInfoModal .delete-book').attr('disabled', 'disabled');
      }
    });
  });
})(window, jQuery);