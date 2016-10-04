define(
  'booktype/blockquote-manager', [
    'aloha',
    'jquery',
    'aloha/ephemera',
    'block/block',
    'block/blockmanager',
    'PubSub'
  ],
  function (Aloha, jQuery, Ephemera, Block, BlockManager, PubSub) {
    var BlockquoteBlock = Block.AbstractBlock.extend({
      title: 'Blockquote',

      isDraggable: function () {
        return false;
      },

      _initBlocks: function ($element) {
        jQuery($element).find('blockquote').each(function () {
          var $elem = jQuery(this);
          if (!jQuery($elem.children(':first')).hasClass('aloha-editable'))
            $elem.wrapInner('<div class="aloha-editable"></div>');
        });
      },

      destroy: function ($element) {
        booktype.utils.confirm({
          width: 310,
          message: booktype._('quote_delete')
        }, function (res) {
          if (res) {
            // we should remove actions before any other thing
            $element.find('.bk-action').parent().remove();

            // now unwrap the content
            var $content = $element.find('.aloha-editable').contents().unwrap();
            $element.mahaloBlock();
            $element.replaceWith($content);
          }
        });
      },

      init: function ($element, postProcessFn) {
        this._initBlocks($element);
        var self = this;
        var qtitle = booktype._('quote_title', 'Quote');

        setTimeout(function () {
          // add the remove action to the title bar
          if (!$element.children(':first').hasClass('bk-quote-info')) {
            $element.prepend('\
              <div class="bk-quote-info"><span class="bk-title">' + qtitle + '</span>\
              <a class="bk-action bk-remove" href="#"><span class="icon-trash">\
              </span></a></div>'
            );
          }

          // bind the remove action here
          var bkRemove = $element.find('.bk-remove');
          bkRemove.off('click');
          bkRemove.on('click', function () {
            self.destroy($element);
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

    return {
      init: function () {
        Ephemera.attributes('data-aloha-block-type', 'contenteditable');
        BlockManager.registerBlockType('BlockquoteBlock', BlockquoteBlock);

        this.bindEvents();
      },

      bindEvents: function () {
        var self = this;

        // deactive quote button
        BlockManager.bind('block-deactivate', function (blocks) {
          var quoteBtn = jQuery('button.action.blockquote');

          if (jQuery(blocks[0].$element[0]).hasClass('bk-blockquote'))
            quoteBtn.removeClass('active');
        });

        // bind block selection to activate/deactive quote button
        BlockManager.bind('block-selection-change', function (blocks) {
          if (blocks.length === 0) return;
          var quoteBtn = jQuery('button.action.blockquote');

          if (jQuery(blocks[0].$element[0]).hasClass('bk-blockquote'))
            quoteBtn.addClass('active');
          else
            quoteBtn.removeClass('active');
        });

        Aloha.bind('aloha-my-undo', function (event, editable) {
          self._initBlockquotes(editable);
        });

        Aloha.bind('aloha-editable-created', function ($event, editable) {
          self._initBlockquotes(editable);
        });
      },

      _initBlockquotes: function (editable) {
        editable.obj.find('blockquote').each(function () {
          var $elem = jQuery(this);
          var $block = jQuery('<div class="bk-blockquote"></div>');

          $block.append($elem.clone());
          $elem.replaceWith($block);
          $block.alohaBlock({ 'aloha-block-type': 'BlockquoteBlock' });
        });
      },

      create: function () {
        var Dom = GENTICS.Utils.Dom;
        var editable = Aloha.getEditableById('contenteditor');
        var range = Aloha.Selection.getRangeObject();

        var $blockHtml = jQuery('<div class="bk-blockquote"> \
          <blockquote><p>' + rangy.getSelection().toHtml() + '</p></blockquote></div>');

        $blockHtml.alohaBlock({ 'aloha-block-type': 'BlockquoteBlock' });
        Dom.removeRange(range);
        Dom.insertIntoDOM($blockHtml, range, editable.obj);

        setTimeout(function () {
          var block = BlockManager.getBlock($blockHtml.attr('id'));
          block.activate();
          Dom.setCursorAfter($blockHtml.find('blockquote p')[0]);

          // this is just to set quote btn selected
          jQuery('button.action.blockquote').addClass('active');
        }, 200);
      },

      clean: function (obj) {
        jQuery('.aloha-block-BlockquoteBlock', jQuery(obj)).each(function () {
          var $block = jQuery(this);

          $block.find('blockquote .aloha-editable').contents().unwrap();
          $block.replaceWith($block.find('blockquote'));
        });
      },
    }
  }
);

define([
  'aloha',
  'aloha/plugin',
  'jquery',
  'jquery19',
  'ui/ui',
  'aloha/ephemera',
  'format/format-plugin',
  'booktype/blockquote-manager'
],
  function(Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, formatPlugin, BlockquoteManager) {
    return Plugin.create('extraformat', {
      init: function() {
        // RemoveFormat option from edit dropdown menu
        UI.adopt('removeFormat', null, {
          click: function() {
            formatPlugin.removeFormat();
            Aloha.Selection.rangeObject.select();
          }
        });

        // Blockquote stuff here
        BlockquoteManager.init();

        UI.adopt('blockquote', null, {
          click: function () {
            // TODO: figure/discuss if we should remove the quote
            // when we click action button and cursor is inside of
            // an already create quote
            BlockquoteManager.create();
          }
        });
      },

      makeClean: function (obj) {
        BlockquoteManager.clean(obj);
      }
    });
  }
);
