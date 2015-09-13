define(
  ['aloha', 'aloha/plugin', 'aloha/engine', 'PubSub', 'jquery', 'jquery19', 'booktype'],
  function (Aloha, Plugin, Engine, PubSub, jQuery, jQuery19, booktype) {

    return Plugin.create(
      'icejs', {

      initICE: function (callback) {
          // if tracker is already initiated, nothing to do here
          if (jQuery('#contenteditor').data('ice-initiated') === true) return {};

          var username = booktype.fullname.length > 0 ? booktype.fullname : booktype.username;

          booktype.tracker = new ice.InlineChangeEditor({
            element: jQuery('#contenteditor')[0],
            handleEvents: true,
            currentUser: {id: booktype.username, name: username},
            customDeleteHandler: function(range, direction){
              // do more research about value param for aloha methods, just faking it for now
              var value = '';

              // direction: left -> backspace delete, right -> forward delete
              var deleteFunc = (direction === 'left') ? window.alohaDelete : window.alohaForwardDelete;
              deleteFunc.action(value, range);
            },
            plugins: [
              {
                name: 'IceCopyPastePlugin',
                settings: {
                  // Tags and attributes to preserve when cleaning a paste
                  preserve: 'p,a[href],span[id,class]em,strong'
                }
              }
            ]
          });

          // set attribute, so we just enable once
          jQuery('#contenteditor').data('ice-initiated', true);

          if (typeof(callback) === 'function')
            callback(booktype.tracker);
      },

      stopAlohaTracking: function () {
        booktype.tracker.disableChangeTracking();

        // restore aloha overridden commands
        Engine.commands.delete = window.alohaDelete;
        Engine.commands.forwarddelete = window.alohaForwardDelete;
      },

      overrideMethods: function () {
        // fake method to avoid double deleting when tracking is On
        var alohaFakeDelete = {
          action: function(value, range) {}
        };

        // backup old delete command
        window.alohaDelete = Engine.commands.delete;
        window.alohaForwardDelete = Engine.commands.forwarddelete;

        // override default methods
        Engine.commands.delete = alohaFakeDelete;
        Engine.commands.forwarddelete = alohaFakeDelete;
      },

      registerEventHandlers: function () {
        // only if mozilla or the active contenteditable is not editor, like title tag or tables
        Aloha.Markup.addKeyHandler(8, function(event){
          if (Aloha.browser.mozilla || event.target !== jQuery('#contenteditor')[0]) {
            return booktype.tracker._handleAncillaryKey(event);
          }
        });

        Aloha.Markup.addKeyHandler(46, function(event){
          if (Aloha.browser.mozilla || event.target !== jQuery('#contenteditor')[0]) {
            return booktype.tracker._handleAncillaryKey(event);
          }
        });
      },

      removeEventHandlers: function () {
        jQuery.each([8, 46], function (idx, keyCode) {
          Aloha.Markup.removeKeyHandler(keyCode);
        });
      },

      init: function () {
        var plugin = this;

        // this bind is to start tracking manually even
        // if booktype.trackChanges is false
        Aloha.bind('aloha-start-tracking', function (e) {
          if (typeof(booktype.tracker) !== 'undefined') {
            booktype.tracker.enableChangeTracking();
            plugin.registerEventHandlers();
          } else {
            plugin.initICE(function (tracker) {
              tracker.startTracking();
              plugin.registerEventHandlers();
              plugin.overrideMethods();
            });
          }
        });

        // if aloha editor gets destroyed, stop tracking engine
        Aloha.bind('aloha-editable-destroyed', function (e, editable) {
          Aloha.bind('aloha-stop-tracking');
        });

        // this is to manually stop tracking changes
        Aloha.bind('aloha-stop-tracking', function () {
          plugin.stopAlohaTracking();
          plugin.removeEventHandlers();
        });

        // accept all changes
        Aloha.bind('aloha-tracking-accept-all', function () {
          booktype.tracker.acceptAll();
        });

        // decline all changes
        Aloha.bind('aloha-tracking-decline-all', function () {
          booktype.tracker.rejectAll();
        });

        // accept one changes
        Aloha.bind('aloha-tracking-accept-one', function () {
          booktype.tracker.acceptChange();
        });

        // decline one changes
        Aloha.bind('aloha-tracking-decline-one', function () {
          booktype.tracker.rejectChange();
        });

        // show / hide changes in editor
        Aloha.bind('aloha-tracking-changes-show', function () {
          jQuery('#contenteditor').removeClass('CT-hide');
        });

        Aloha.bind('aloha-tracking-changes-hide', function () {
          jQuery('#contenteditor').addClass('CT-hide');
        });
      },

      makeClean: function (obj) {
        jQuery(obj).find('span.del, span.ins').each(function () {
          var $elem = jQuery(this);

          // first, replace &nbsp; with real white spaces
          $elem.html($elem.html().replace(/&nbsp;/gi, " "));

          // then, clean some other things
          $elem.find('span.nbsp').replaceWith(" ");
        });
      }
    });
  }
);