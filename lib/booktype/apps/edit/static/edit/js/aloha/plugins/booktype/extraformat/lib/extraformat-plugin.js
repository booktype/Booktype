define(
  'booktype/blockquote-manager', [
    'aloha',
    'jquery',
    'aloha/ephemera',
    'block/block',
    'block/blockmanager',
    'PubSub',
    'booktype'
  ],
  function (Aloha, jQuery, Ephemera, Block, BlockManager, PubSub, booktype) {
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

            booktype.editor.edit.disableSave(false);
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
              <a class="bk-action bk-remove" href="#"><span class="fa fa-trash">\
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

          // @NOTE: this is a workaround to avoid issues when changing focus
          // over custom blocks and last keyCode of editor
          var editable = Aloha.getActiveEditable();
          if (editable)
            editable.keyCode = null;
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
        if (!editable || !editable.obj) return;

        editable.obj.find('blockquote').each(function () {
          var $elem = jQuery(this);
          var $block = jQuery('<div class="bk-blockquote"></div>');

          $block.append($elem.clone());
          $elem.replaceWith($block);
          $block.alohaBlock({ 'aloha-block-type': 'BlockquoteBlock' });
        });
      },

      create: function (quotedContent, author) {
        var Dom = GENTICS.Utils.Dom;
        var editable = Aloha.getEditableById('contenteditor');
        var range = Aloha.Selection.getRangeObject();

        if (jQuery(quotedContent).find('p').length === 0)
          quotedContent = '<p>' + quotedContent + '</p>';

        var html = ['<div class="bk-blockquote"><blockquote>', quotedContent];
        if (author.length > 0)
          html.push('<p class="bk-cite">' + author.trim() + '<p>');
        html.push('</blockquote></div>');

        $blockHtml = jQuery(html.join(''));

        $blockHtml.alohaBlock({ 'aloha-block-type': 'BlockquoteBlock' });
        Dom.removeRange(range);
        Dom.insertIntoDOM($blockHtml, range, editable.obj);

        // let's remove the empty paragraphs
        $blockHtml.find('p:empty').remove();

        setTimeout(function () {
          var block = BlockManager.getBlock($blockHtml.attr('id'));
          block.activate();
          Dom.setCursorAfter($blockHtml.find('blockquote p')[0]);

          // this is just to set quote btn selected
          jQuery('button.action.blockquote').addClass('active');

          booktype.editor.edit.disableSave(false);
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
  'react',
  'react-dom',
  'booktype/blockquote-manager',
  'jsx!extraformat/extraformat-components'
],
  function(
    Aloha, Plugin, jQuery, jQuery19, UI,
    Ephemera, formatPlugin, React, ReactDOM,
    BlockquoteManager, QuoteComponents
  ) {
    return Plugin.create('extraformat', {
      init: function() {
        var plugin = this;

        // RemoveFormat option from edit dropdown menu
        UI.adopt('removeFormat', null, {
          click: function() {
            formatPlugin.removeFormat();
            Aloha.Selection.rangeObject.select();
          }
        });

        // Blockquote stuff here
        BlockquoteManager.init();

        // we need to mount the needed components here
        var quoteModal = React.createElement(QuoteComponents.InsertBlockquoteModal, {});
        plugin.quoteModal = ReactDOM.render(quoteModal, document.getElementById('blockquoteModal'));

        UI.adopt('blockquote', null, {
          click: function () {
            var activeBlock = jQuery('.aloha-block-BlockquoteBlock.aloha-block-active');
            if (jQuery(this).hasClass('active') && activeBlock.length > 0)
              activeBlock.find('.bk-remove').click();
            else {
              var quotedContent = rangy.getSelection().toHtml();
              plugin.quoteModal.show(quotedContent);
            }
          }
        });
      },

      makeClean: function (obj) {
        BlockquoteManager.clean(obj);
      }
    });
  }
);
