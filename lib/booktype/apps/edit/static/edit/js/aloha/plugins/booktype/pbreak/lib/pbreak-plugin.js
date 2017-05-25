define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block', 'block/blockmanager'],
  function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, block, BlockManager) {

    var editable = null,
      range = null,
      selectedBlock = null;

      // Define Page Break Block
    var BreakBlock = block.AbstractBlock.extend({
      title: 'Page Break',
      isDraggable: function () {
        return false;
      },
      init: function ($element, postProcessFn) {
        // Will erase if anything is inside and insert small icon while we are
        // editing this content.
        var $this = this;

        $element.empty().append('<i class="fa fa-ellipsis-h"></i>');

        $element.on('click', function () {
          selectedBlock = $this;
          jQuery19('#modalPageBreak').modal('show');
          return false;
        });

        return postProcessFn();
      },
      update: function ($element, postProcessFn) {
        return postProcessFn();
      }
    });

    return Plugin.create('pbreak', {
      makeClean: function (obj) {
        jQuery(obj).find('.aloha-block-BreakBlock').each(function () {
          var $this = jQuery(this);
          $this.replaceWith('<div class="page-break"></div>');
        });
      },
      init: function () {
        // Register this block
        BlockManager.registerBlockType('BreakBlock', BreakBlock);

        // When editor is initialised check if there is any page break in our content.
        // If there is initiate Page Break Block for each of the elements.
        Aloha.bind('aloha-editable-created', function ($event, editable) {
          editable.obj.find('DIV.page-break').alohaBlock({'aloha-block-type': 'BreakBlock'});
        });

        Aloha.bind('aloha-my-undo', function (event, args) {
          args.editable.obj.find('DIV.page-break').alohaBlock({'aloha-block-type': 'BreakBlock'});
        });

        jQuery19('#modalPageBreak').find('.operation-remove').on('click', function () {
          selectedBlock.$element.remove();
          jQuery19('#modalPageBreak').modal('hide');
        });

        jQuery19('#modalPageBreak').find('.operation-cancel').on('click', function () {
          jQuery19('#modalPageBreak').modal('hide');
        });

        UI.adopt('pbreak', null, {
          click: function() {
            editable = Aloha.activeEditable;
            range = Aloha.Selection.getRangeObject();

            // Insert div element inside with a certain class
            // After that, create Page Break Block out of it
            var $a = jQuery('<div class="page-break"></div>');
            $a.alohaBlock({'aloha-block-type': 'BreakBlock'});

            GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);

            range.select();
          }
        });
      }
    });
  }
);
