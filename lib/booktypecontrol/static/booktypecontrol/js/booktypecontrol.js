(function (win, $) {
  'use strict';
  
  win.booktype.controlcenter = {
    init: function () {

      // set settings active tab
      var activeTab = $('#settings').data('active-tab');
      $('#settings')
        .find('a[href="#' + activeTab + '"]')
        .parent().addClass('active');

      // start backbone router for control center
      var ControlCenterRouter = Backbone.Router.extend({
        routes: {
          ':option':    'handleSetting'
        },

        handleSetting: function (option) {
          if (win.location.href.indexOf('/_control/new/settings/') > -1) {
            if (ALLOWED_MODULES.indexOf(option) > -1) {
              $.get('?option=' + option, function (data) {
                $('#settings_container').html(data);
              });

              // deactivate current tab
              $('#settings').find('li.active').removeClass('active');
              $('#settings').find('li:has(a[href="#' + option + '"])').addClass('active');
            }
          } else {
            win.location.href = '/_control/new/settings/#' + option;
          }
          
        }
      });

      // initialize the dashboard router
      var router = new ControlCenterRouter();

      // Start Backbone history, necessary for bookmarkable URL's
      Backbone.history.start();

      $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var option = $(e.target).attr('href');
        router.navigate(option, { trigger: true });
        return false;
      });

      // remove modal data
      $('body').on('hide.bs.modal', '#personInfoModal', function () {
        $(this).removeData('bs.modal').html('');
      });

    }
  };

  $(function () {
    win.booktype.controlcenter.init();
  });

})(window, jQuery);