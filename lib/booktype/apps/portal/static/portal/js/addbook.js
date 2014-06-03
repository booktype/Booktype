(function (win, jquery) {
  'use strict';
  win.booktype.addbook = {
    init: function () {

      jquery(document).on('shown.bs.modal', '#addBookModal', function () {
        jquery('.btn-primary').click(function () {
          var groupName = jquery(this).attr('group-name-url');
          var selectedBooks = jquery('.selected-book:checked').map(function () {
            return jquery(this).val();
          }).get();
          win.booktype.initCSRF();

          jquery.post(groupName, {
              task: 'add-book',
              books: selectedBooks.toString()
            }, function () {
              location.reload();
            });
        });
      });
    }
  };

  // on ready
  jquery(function () {
    win.booktype.addbook.init();
  });
})(window, jQuery);