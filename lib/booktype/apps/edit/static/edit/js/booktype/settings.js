(function (win, $) {
  'use strict';
  
  $.namespace('win.booktype.editor.settings');

  win.booktype.editor.settings = (function () {

    var SettingsRouter = Backbone.Router.extend({
      routes: {
        'settings': 'settings',
        'settings/:module': 'loadSetting'
      },

      settings: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['settings'];
          win.booktype.editor.data.activePanel.show();
        });
      },

      loadSetting: function (module) {
        if (win.booktype.editor.settings.uiLoaded === undefined) {
          this.settings();
        }

        // TODO: check if module is valid

        // check if base content has been loaded

        // load corresponding module
        var params = {
          'setting': module,
          'bookid': win.booktype.currentBookID
        };

        win.booktype.ui.notify('Loading section');

        $.get(win.booktype.bookSettingsURL + '?' + $.param(params),
          function (html) {
            $('#setting_content').html(html);
          }).error(function () {
            var notAvailable = win.booktype.ui.getTemplate('templateModuleNotAvailable');
            $('#setting_content').html(notAvailable);
          }).complete(function () {
            win.booktype.ui.notify();
          }
        );
      }
    });

    var router = new SettingsRouter();

    var _show = function () {
      var header = win.booktype.ui.getTemplate('templateSettingsHeader');
      $('DIV.contentHeader').html(header);

      var t = win.booktype.ui.getTemplate('templateSettingsContent');
      $('#content').html(t).addClass('settings');

      win.booktype.editor.settings.uiLoaded = true;
    };

    var _hide = function (callback) {
      // Destroy tooltip
      $('DIV.contentHeader [rel=tooltip]').tooltip('destroy');

      // Clear content
      $('#content').empty();
      $('DIV.contentHeader').empty();
        
      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    var _init = function () {
      $('#button-settings').on('change', function () { Backbone.history.navigate('settings', true); });

      $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
        // trigger url via backbone router
        var option = $(e.target).attr('href').replace('#', '');
        router.navigate('settings/' + option, { trigger: true });
        return false;
      });
    };

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'name': 'settings'
    };
  })();

})(window, jQuery);