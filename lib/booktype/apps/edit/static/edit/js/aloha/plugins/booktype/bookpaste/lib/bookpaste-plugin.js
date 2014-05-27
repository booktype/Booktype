define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'underscore', 'booktype', 'PubSub', 'aloha/contenthandlermanager'],
  function (Aloha, Plugin, jQuery,  jQuery19, UI, Ephemera, _, booktype, PubSub, ContentHandlerManager) {
    'use strict';

    /*  
      Purpose of this plugin is to check what is user pasting and erase references to external
      resources like images and etc.
    */

    var replaceImage = function () {
      var $img = jQuery(this);

      var src = $img[0].src;
      var bookURL = _.sprintf('%s/%s/', booktype.baseURL, booktype.currentBookURL);

      // If we are doing copy + paste of our own material images will get
      // absolute path instead of relative as defined in src attribute.
      // This is why we want to remove it.

      if (_(src).startsWith(bookURL)) {
        src = src.replace(bookURL, '');

        if (_(src).startsWith('_edit/')) {
          src = src.replace('_edit/', '');
        }

        $img.attr('src', src);
      }

      if (_(src).startsWith('http://') || _(src).startsWith('https://')) {
        $img.replaceWith('<span class="external-resource">' + src + '</span>');
      }
    };

    var ImagelessPasteHandler = ContentHandlerManager.createHandler({
      enabled: true,
      handleContent: function (content) {
        var $content;

        if (typeof content === 'string') {
          $content = jQuery('<div>' + content + '</div>');
        } else if (content instanceof jQuery) {
          $content = jQuery('<div>').append(content);
        }

        $content.find('img').each(replaceImage);

        return $content.html();
      }
    });

    return Plugin.create('bookpaste', {
      defaultSettings: {
        enabled: true,
        imageCallback: replaceImage // Can be overwritten by user in configuration
      },

      init: function () {
        var self = this;

        self.settings = jQuery.extend(true, self.defaultSettings, self.settings);

        if (!self.settings.enabled) { return; }

        ContentHandlerManager.register('formatless', ImagelessPasteHandler);
      }
    });
  }
);