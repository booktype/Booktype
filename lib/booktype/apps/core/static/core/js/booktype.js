$(function(){
  // enable tooltips
  $('[rel=tooltip]').tooltip({container: 'body'});

  // use button tag as link with trigger url attribute
  $('button[data-href]').click(function(){
    window.location.href = $(this).data('href');
  });

  // TODO: we probably need to create a better structure for the 
  // javascript code (maybe plugins or use a existing library)

  // related with Book Info Page
  $('body').on('hidden.bs.modal', '.bookInfoModal', function () {
    $(this).removeData('bs.modal').html('');
  });

  // Delete Book
  $('body').on('keyup paste', '.bookInfoModal input[name="title"]', function() {
    if($(this).val() === $(this).attr("placeholder")) {
      $('.bookInfoModal .delete-book').removeAttr("disabled");
    } else {
      $('.bookInfoModal .delete-book').attr('disabled', 'disabled');
    } 
  });
});