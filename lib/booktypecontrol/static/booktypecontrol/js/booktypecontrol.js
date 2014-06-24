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
          $.get('?option=' + option, function (data) {
            $('#settings_container').html(data);
          });

          // deactivate current tab
          console.log($('#settings').find('li.active'));
          $('#settings').find('li.active').removeClass('active');

          $('#settings').find('li:has(a[href="#' + option + '"])').addClass('active');
          return false;
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

    }
  };

  $(function () {
    win.booktype.controlcenter.init();
  });

})(window, jQuery);