define(
  ['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block',
    'block/blockmanager', 'underscore', 'endnotes/block', 'toolbar/toolbar-plugin', 'PubSub'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, block, BlockManager, _, EndnotesBlock, toolbar, PubSub) {
    "use strict";

    var $blockInstance;

    var _initHeadings = function (editable, unmodify) {
      var $endnotes = editable.obj.find('ol.endnotes');

      if ($endnotes.length > 0) {
        $endnotes.wrap('<div></div>');
        $endnotes.parent().alohaBlock({'aloha-block-type': 'EndnoteBlock'});
        if (_.isUndefined($blockInstance)) {
          $blockInstance = BlockManager.getBlock(jQuery('.aloha-block-EndnoteBlock:first'));
        }
      }
    };

    return Plugin.create('endnotes', {
      defaultSettings: {
        enabled: false,
        supForbiddenContainer: ['sup'],
        disabledButtons: ['currentHeading', 'changeHeading', 'insertImage', 'table-dropdown', 'alignLeft',
                          'alignJustify', 'alignRight', 'alignCenter', 'unorderedList', 'orderedList',
                          'indent-left', 'indent-right']
      },
      init: function () {
        var editable, range;
        var $this = this;
        this._menuInsertEndnote = null;

        // merge settings
        $this.settings = jQuery.extend(true, $this.defaultSettings, $this.settings);

        // allow aloha-block-type be editable
        Ephemera.attributes('data-aloha-block-type', 'contenteditable');

        // register block
        BlockManager.registerBlockType('EndnoteBlock', EndnotesBlock.EndnoteBlock);

        // subscribe to cursor context changing
        PubSub.sub('aloha.selection.context-change', function (message) {
          if(!$this._menuInsertEndnote) {return;}

          // disable insert endnote link if cursor inside endnotes block or in the forbidden tag
           if (jQuery(message.range.endContainer).closest('div.endnoteText').length) {
             toolbar.disableMenu('endnote-insert');
           } else {
             for (var i = 0; i < $this.settings.supForbiddenContainer.length; i++) {
               if (jQuery(message.range.endContainer).closest($this.settings.supForbiddenContainer[i]).length) {
                 toolbar.disableMenu('endnote-insert');
                 return;
               }
             }
             toolbar.enableMenu('endnote-insert');
           }
        });

        // subscribe to events
        Aloha.bind('aloha-my-undo', function (event, args) {
          _initHeadings(args.editable, false);
        });

        Aloha.bind('aloha-editable-created', function ($event, editable) {
          $this._menuInsertEndnote = jQuery('.contentHeader .btn-toolbar .endnote-insert');
          _initHeadings(editable, true);
        });

        BlockManager.bind('block-activate', function (blocks) {
          _.each(blocks, function (block) {
            if (block.title === 'EndnoteBlock') {
              _.each($this.settings.disabledButtons, function (btn) { toolbar.disableToolbar(btn); });
            }
          });
        });

        BlockManager.bind('block-deactivate', function (blocks) {
          _.each(blocks, function (block) {
            if (block.title === 'EndnoteBlock') {
              _.each($this.settings.disabledButtons, function (btn) { toolbar.enableToolbar(btn); });
            }
          });
        });

        // handle menu link click
        UI.adopt('endnote-insert', null, {
          click: function () {
            editable = Aloha.activeEditable;
            range = Aloha.Selection.getRangeObject();
            $blockInstance = BlockManager.getBlock(jQuery('.aloha-block-EndnoteBlock:first'));

            // check if we try to insert endnote into unallowed tag
            if (jQuery.inArray(range.commonAncestorContainer.tagName.toLowerCase(),
                $this.settings.supForbiddenContainer) !== -1){ return; }

            // whether we inside normal editor or in endnotes block
            if (jQuery(range.limitObject).hasClass('endnoteText')) { return; }

            // get timestamp
            var unique_id = (new Date()).getTime();

            var $sup = jQuery('<sup class="endnote" data-id="' + unique_id + '">#2#</sup>');
            GENTICS.Utils.Dom.insertIntoDOM($sup, range, editable.obj, true);
            range.select();

            if (_.isUndefined($blockInstance)) {
              var $blockDonor = jQuery('<div><ol class="endnotes"></ol></div>');

              Aloha.getEditableById('contenteditor').obj.append($blockDonor);
              $blockDonor.alohaBlock({'aloha-block-type': 'EndnoteBlock'});
              $blockInstance = BlockManager.getBlock(jQuery('.aloha-block-EndnoteBlock:first'));
            }

            // last endnote indicator
            $blockInstance.attr('one', unique_id);

            // focus just inserted endnote and activate block
            $blockInstance.$element.find('div[data-id="' + unique_id +'"] div.aloha-editable').focus();
            $blockInstance.makeActive();

            // scroll to block
            var _top = jQuery19(jQuery19('.aloha-block-EndnoteBlock')).offset().top - jQuery19("#contenteditor").offset().top;
            jQuery19(window).scrollTop(_top - 100);
          }
        });
      },
      makeClean: function (obj) {
        if (!_.isUndefined($blockInstance)) {
          $blockInstance.recalculate();
        }

        jQuery(obj).find('.aloha-block-EndnoteBlock').each(function () {
          var $_this = jQuery(this);

          var $ol = jQuery('<ol class="endnotes"></ol>');
          $ol.attr('dir', window.booktype.bookDir);

          // convert div based data to list-based
          $_this.find('div.elem').each(function (idxm, el) {
            var $el = jQuery(el);
            var content = $el.find('.endnoteText').html();

            if ($el.hasClass('orphan-endnote')) {
              $ol.append('<li class="orphan-endnote">' + content + '</li>')
            } else {
              $ol.append('<li id="endnote-' + $el.attr('data-id') + '">' + content + '</li>')
            }
          });
          $_this.replaceWith($ol);
        });
      }
    });

  }
);
