(function (win, $) {
  'use strict';

  $(function () {
    // Delete Book
    $(document).on('click', 'a.delete-book', function (e) {
      e.preventDefault();
      var el = $(this);

      $.get(el.attr('data-perms'), function (dta) {
        if (dta.admin || _.contains(dta.permissions, 'edit.delete_book')) {
          $('#bookThumbModal').modal({
            placement: 'bottom',
            remote: el.attr('data-remote')
          });
        } else{
          alert(win.booktype._('no_book_delete_permission', 'You have no permission to delete this book'));
        }
      });
    });

    $(document).on('keyup paste', '.bookInfoModal input[name="title"]', function () {
      if ($(this).val() === $(this).attr('placeholder')) {
        $('.bookInfoModal .delete-book').removeAttr('disabled');
      } else {
        $('.bookInfoModal .delete-book').attr('disabled', 'disabled');
      }
    });
  });
})(window, jQuery);
