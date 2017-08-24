define([
  'aloha',
  'aloha/plugin',
  'jquery',
  'jquery19',
  'ui/ui',
  'aloha/ephemera',
  'block/block',
  'block/blockmanager',
  'booktype',
],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, Block, BlockManager, booktype) {
    'use strict';

    var InfoBoxBlock = Block.AbstractBlock.extend({
      title: 'InfoBox',
      isDraggable: function () {
        return false;
      },

      _initBlocks: function ($element) {
        jQuery($element).find('.box-caption, .box-content').each(function () {
          var $elem = jQuery(this);
          if (!jQuery($elem.children(':first')).hasClass('aloha-editable'))
            $elem.wrapInner('<div class="aloha-editable"></div>');
        });
      },

      init: function ($element, postProcessFn) {
        this._initBlocks($element);

        setTimeout(function () {
          // add the remove action to the title bar
          var caption = jQuery19($element).find('.box-caption');
          if (caption.find('.bk-action').length === 0)
            caption.prepend('<a class="bk-action bk-remove" href="#"><span class="fa fa-trash"></span></a>');

          // bind the remove action here
          var bkRemove = jQuery19($element).find('.bk-remove');
          bkRemove.off('click');
          bkRemove.on('click', function () {
            booktype.utils.confirm({
              width: 310,
              message: booktype._('infobox_delete')
            }, function (res) {
              if (res) {
                // we should remove actions before any other thing
                $element.find('.bk-action').remove();

                // now unwrap the content
                var $content = $element.find('.aloha-editable').contents().unwrap();
                $element.mahaloBlock();
                $element.replaceWith($content);
              }
            });
            return false;
          });
        }, 300);

        return postProcessFn();
      },

      update: function ($element, postProcessFn) {
        this._initBlocks($element);
        return postProcessFn();
      }
    });

    return Plugin.create('infobox', {

      // write all the crazy stuff
      init: function () {
        var plugin = this;

        plugin.settings = jQuery19.extend(true, plugin.defaultSettings, plugin.settings);

        // return if plugin not enabled
        if (!plugin.settings.enabled) { return; }

        // let's wire all the events that we want to listen
        plugin.bindEvents();

        Ephemera.attributes('data-aloha-block-type', 'contenteditable');
        BlockManager.registerBlockType('InfoBoxBlock', InfoBoxBlock);

        UI.adopt('infobox-insert', null, {
          click: function () {
            jQuery19('#infoboxDialog').modal('show');
            return true;
          }
        });
      },

      bindEvents: function () {
        var plugin = this;
        var $dialog = jQuery19('#infoboxDialog');

        $dialog.find('.btn-insert').on('click', function () {
          var editable = Aloha.getEditableById('contenteditor');
          var range = Aloha.Selection.getRangeObject();
          var boxTitle = $dialog.find('input[name="box-title"]').val();

          var $infoboxHtml = jQuery('<div class="bk-box"><div class="box-caption">\
            <p>' + boxTitle + '</p></div><div class="box-content"><p></p></div></div>');

          $infoboxHtml.alohaBlock({ 'aloha-block-type': 'InfoBoxBlock' });

          GENTICS.Utils.Dom.insertIntoDOM($infoboxHtml, range, editable.obj);

          $dialog.modal('hide');

          setTimeout(function () {
            var block = BlockManager.getBlock($infoboxHtml.attr('id'));
            block.activate();
          }, 200);
        });

        $dialog.on('shown.bs.modal', function (event) {
          var boxTitle = $dialog.find('input[name="box-title"]');
          boxTitle.val('');
          boxTitle.focus();
        });

        Aloha.bind('aloha-my-undo', function (event, editable) {
          if (!editable) return;
          plugin._initInfoBoxes(editable);
        });

        Aloha.bind('aloha-editable-created', function (event, editable) {
          plugin._initInfoBoxes(editable);
        });
      },

      _initInfoBoxes: function (editable) {
        if (!editable || !editable.obj) return;

        editable.obj.find('div.bk-box').each(function () {
          var $block = jQuery(this);
          $block.alohaBlock({ 'aloha-block-type': 'InfoBoxBlock' });
        });
      },

      makeClean: function (obj) {
        jQuery19('.aloha-block-InfoBoxBlock', jQuery19(obj)).each(function () {
          var $block = jQuery19(this);

          // remove actions
          $block.find('.bk-action').remove();

          $block.find('.box-caption, .box-content').each(function () {
            var $elems = jQuery19(this).find('div').html();
            jQuery19(this).html($elems);
          });

          var newElem = jQuery('<div class="bk-box">' + $block.html() + '</div>');
          $block.replaceWith(newElem);
        });
      }
    });
  }
);
