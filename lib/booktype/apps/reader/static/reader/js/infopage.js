(function (win, $) {
  'use strict';

  $(function () {
    // Delete Book
    $(document).on('click', 'a.delete-book', function (e) {
      e.preventDefault();
      var el = $(this);

      $.get(el.attr('data-perms'), function (dta) {
        if (dta.admin || _.contains(dta.permissions, 'edit.delete_book')) {
          var url = el.attr('data-remote');
          $('#bookThumbModal')
            .load(url)
            .modal({ placement: 'bottom', show: true });
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

    $(document).on('click', '#downloadEpubSkeleton', function (e) {
      var self = this;

      win.booktype.utils.confirm({
        message: win.booktype._('downloadEpubSkeletonMessage'),
        alertTitle: win.booktype._('downloadEpubSkeletonTitle'),
        acceptText: win.booktype._('downloadEpubSkeletonConfirmBtn'),
        width: 370
      }, function () {
        win.location.href = $(self).data('url');
      });
    });
  });
})(window, jQuery);
