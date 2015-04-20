(function (win, $) {
  'use strict';

  win.booktype.controlcenter = {
    init: function () {
      var controlcenter = this;

      // set settings active tab
      var activeTab = $('#settings').data('active-tab');
      $('#settings')
        .find('a[href="#' + activeTab + '"]')
        .parent().addClass('active');

      // start backbone router for control center
      var ControlCenterRouter = Backbone.Router.extend({
        routes: {
          ':option': 'handleSetting'
        },

        handleSetting: function (option) {
          if (win.location.href.indexOf(CONTROL_CENTER_URL) > -1) {

            if (ALLOWED_MODULES.indexOf(option) > -1) {
              win.booktype.initCSRF();

              $.get('?option=' + option, function (data) {
                $('#settings_container')
                  .html(data)
                  .removeClass('hide');
              });

              // deactivate current tab
              $('#settings').find('li.active').removeClass('active');
              var tabOption = $('#settings').find('li a[href="#' + option + '"]');
              tabOption.parent().addClass('active');

              // set control center menu option active
              controlcenter.setActiveMenu(tabOption);

              // scroll to top of page
              $('html, body').animate({
                scrollTop: 0
              }, 400);
            }

          } else {
            win.location.href = CONTROL_CENTER_URL + '#' + option;
          }
        }
      });

      // initialize the dashboard router
      var router = new ControlCenterRouter();

      // Start Backbone history, necessary for bookmarkable URL's
      Backbone.history.start();

      $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        // trigger url via backbone router
        var option = $(e.target).attr('href');
        router.navigate(option, {
          trigger: true
        });
        return false;
      });

      // switch books layout
      $(document).on('click', '.showList', function () {
        $('#books-prew, #books-prew-2').attr('class', 'book-list');
      });

      $(document).on('click', '.showGrid', function () {
        $('#books-prew, #books-prew-2').attr('class', 'book-thumb');
      });

      // enable popover for books
      $(document).on('click', '.book-info h4 > a', function () {
        var self = this;
        var isCurrentActive = $(this).hasClass('active_popover');

        $('.active_popover')
          .removeClass('active_popover')
          .popover('hide');

        if (!isCurrentActive) {
          $(self).popover({
            trigger: 'focus',
            placement: 'top',
            html: true,
            container: 'body',
            content: function () {
              var toolbar = $(self).closest('.book-info').find('.control_center_btns').clone();
              return toolbar.removeClass('pull-right');
            }
          });

          $(self).popover('show');
          $(self).addClass('active_popover');
        }
        return false;
      });

      // remove all popovers when focus in other place
      $(document).on('click', ':not(.book-info h4 > a)', function () {
        $('.book-info h4 > a').each(function (id, elem) {
          if ($(elem).data('bs.popover') !== undefined) {
            $(elem).popover('hide');
            $(elem).removeClass('active_popover');
          }
        });
      });

      // check if module option in url
      if (!window.location.hash) {
        $('#settings_container').removeClass('hide');
        controlcenter.setActiveMenu($('#settings a[href="#site-description"]'));
      }

    },

    setActiveMenu: function (elem) {
      // set control center menu active
      var menu = $(elem).parent().prevAll('h4:first').data('menu') || 'settings';

      // disable current active menu
      $('#control-menu button.active').removeClass('active');

      // set current active
      $('#control-menu').find('button[data-menu="' + menu + '"]').addClass('active');

      // disable current active option in side menu
      $('#collapsed-admin-menu li.active').removeClass('active');

      // set current active in side menu
      $('#collapsed-admin-menu').find('li[data-menu="' + menu + '"]').addClass('active');
    }
  };

  $(function () {
    win.booktype.controlcenter.init();
  });

})(window, jQuery);